import os
from rest_framework import status
from rest_framework.request import Request
from rest_framework.response import Response

from .models import Image, ExpiringImage
from PIL import Image as PILImage


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
