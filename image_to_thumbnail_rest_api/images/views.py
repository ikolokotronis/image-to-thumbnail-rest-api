import os
from typing import Callable

from rest_framework import status
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView
from django.core.exceptions import ObjectDoesNotExist

from .models import Image, ExpiringImage
from .serializers import ImageSerializer
from PIL import Image as PILImage

from users.models import User


class ImageProcessor:

    def __image_processing(self, request: Request, image_instance: Image, image: PILImage, size: int) -> tuple:
        """
        Processes image, returns file url and file extension.
        """
        original_image_url = image_instance.original_image.url
        image_url, image_extension = os.path.splitext(original_image_url)
        image.thumbnail((image.width, size))
        image.save(f".{image_url}_{size}px_thumbnail{image_extension}")
        return image_url, image_extension

    def basic_tier_processing(self, request: Request, image_instance: Image, image: PILImage) -> Response:
        """
        Basic tier processing.
        """
        image_url, image_extension = self.__image_processing(
            request, image_instance, image, 200
        )
        data = {
            "200px_thumbnail": f"{image_url}_200px_thumbnail{image_extension}",
            "success": "Image uploaded successfully",
        }
        return Response(data, status=status.HTTP_201_CREATED)

    def premium_tier_processing(self, request: Request, image_instance: Image, image: PILImage) -> Response:
        """
        Premium tier processing.
        """
        image_url, image_extension = self.__image_processing(
            request, image_instance, image, 400
        )
        image_url, image_extension = self.__image_processing(
            request, image_instance, image, 200
        )
        data = {
            "400px_thumbnail": f"{image_url}_400px_thumbnail{image_extension}",
            "200px_thumbnail": f"{image_url}_200px_thumbnail{image_extension}",
            "original_image": image_instance.original_image.url,
            "success": "Image uploaded successfully",
        }
        return Response(data, status=status.HTTP_201_CREATED)

    def enterprise_tier_processing(self, request: Request, image_instance: Image, image: PILImage) -> Response:
        """
        Enterprise tier processing.
        """
        try:
            live_time = request.data["live_time"]
        except KeyError:
            return Response(
                {"error": "No live_time field"}, status=status.HTTP_400_BAD_REQUEST
            )
        if int(live_time) < 300 or int(live_time) > 3000:
            return Response(
                {"error": "Live time must be between 300 and 3000 seconds"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        original_image_url = image_instance.original_image.url
        image_url, image_extension = self.__image_processing(
            request, image_instance, image, 400
        )
        image_url, image_extension = self.__image_processing(
            request, image_instance, image, 200
        )
        image_name = os.path.splitext(os.path.basename(original_image_url))[0]
        expiring_image = ExpiringImage.objects.create(
            user=request.user, live_time=live_time
        )
        expiring_image.image.save(
            f"{image_name}{image_extension}", image_instance.original_image
        )
        data = {
            "400px_thumbnail": f"{image_url}_400px_thumbnail{image_extension}",
            "200px_thumbnail": f"{image_url}_200px_thumbnail{image_extension}",
            "original_image": original_image_url,
            f"{live_time}s_expiring_link": expiring_image.image.url,
            "success": "Image uploaded successfully",
        }
        return Response(data, status=status.HTTP_201_CREATED)

    def default_tier_processing(self, request: Request, image_instance: Image, image: PILImage) -> Response:
        """
        Default tier processing. (for arbitrary tiers)
        """
        user = request.user
        image_url, image_extension = self.__image_processing(
            request, image_instance, image, user.tier.thumbnail_height
        )
        image_name = os.path.basename(image_url)
        data = {
            f"{str(user.tier.thumbnail_height)}px_thumbnail": f"{image_url}_{str(user.tier.thumbnail_height)}px_thumbnail{image_extension}"
        }
        if user.tier.presence_of_original_file_link:
            data["original_image"] = image_instance.original_image.url
        if user.tier.ability_to_fetch_expiring_link:
            try:
                live_time = request.data["live_time"]
            except KeyError:
                return Response(
                    {"error": "No live_time field"}, status=status.HTTP_400_BAD_REQUEST
                )
            if int(live_time) < 300 or int(live_time) > 3000:
                return Response(
                    {"error": "Live time must be between 300 and 3000 seconds"},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            expiring_image = ExpiringImage.objects.create(
                user=user, live_time=live_time
            )
            expiring_image.image.save(
                f"{image_name}{image_extension}", image_instance.original_image
            )
            data[f"{live_time}s_expiring_link"] = expiring_image.image.url
        data["success"] = "Image uploaded successfully"
        return Response(data, status=status.HTTP_201_CREATED)


class ImageView(APIView):
    # authentication_classes = [TokenAuthentication]
    # permission_classes = [IsAuthenticated]

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.image_processor = ImageProcessor()
        self.options = {
            "Basic": self.image_processor.basic_tier_processing,
            "Premium": self.image_processor.premium_tier_processing,
            "Enterprise": self.image_processor.enterprise_tier_processing,
        }

    def get(self, request: Request) -> Response:
        """
        Lists all images.
        """
        images = Image.objects.filter(user_id=request.user.id)
        if images:
            serializer = ImageSerializer(images, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response({"No images found"}, status=status.HTTP_404_NOT_FOUND)

    def post(self, request: Request) -> Response | Callable:
        """
        Calls the appropriate tier processing method and returns the response.
        """
        user = request.user
        image_instance = Image(user=user)
        serializer = ImageSerializer(image_instance, data=request.data)
        if serializer.is_valid():
            serializer.save()
            image_format = os.path.splitext(image_instance.original_image.url)[1]
            if image_format not in [".jpg", ".jpeg", ".png"]:
                image_instance.delete()
                return Response(
                    {"error": "Image format not supported"},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            original_image_path = image_instance.original_image.path
            with PILImage.open(original_image_path) as image:
                return self.options.get(user.tier.name, self.image_processor.default_tier_processing)(request, image_instance, image)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
