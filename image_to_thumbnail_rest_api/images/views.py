import os
from datetime import datetime
from typing import Callable

from django.http import HttpResponse
from rest_framework import status
from rest_framework.authentication import SessionAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView
from django.core.exceptions import ObjectDoesNotExist

from .image_processor import ImageProcessor
from .models import Image, ExpiringImage
from .serializers import ImageSerializer
from PIL import Image as PILImage

from users.models import User


class ImageView(APIView):
    authentication_classes = [SessionAuthentication]
    permission_classes = [IsAuthenticated]

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


class ExpiringImageView(APIView):

    def __image_has_expired(self, image: ExpiringImage) -> bool:
        """
        If image has expired, return true.
        """
        current_time_in_seconds = int(datetime.now().timestamp())
        image_creation_time = int(image.created_at.timestamp())
        if current_time_in_seconds - image_creation_time > int(image.live_time):
            return True
        return False

    def __open_image(self, file_path: str) -> HttpResponse | Response:
        if os.path.exists(file_path):
            with open(file_path, "rb") as f:
                image_data = f.read()
                return HttpResponse(image_data, content_type="image/jpeg")
        return Response({"error": "Image not found"}, status=status.HTTP_404_NOT_FOUND)

    def get(self, request: Request, file_name: str) -> Response | Callable:
        try:
            image = ExpiringImage.objects.get(image=f"expiring-images/{file_name}")
        except ObjectDoesNotExist:
            return Response(
                {"error": "Image does not exist"}, status=status.HTTP_404_NOT_FOUND
            )
        if self.__image_has_expired(image):
            image.delete()
            return Response(
                {"error": "Image has expired"}, status=status.HTTP_404_NOT_FOUND
            )
        file_path = os.path.join(os.path.dirname(image.image.path), file_name)
        return self.__open_image(file_path)



class OpenImageView(APIView):
    """
    Image access management.
    Only the owner of the image can access the image, if it exists.
    """

    authentication_classes = [SessionAuthentication]
    permission_classes = [IsAuthenticated]

    def __authorize_user(self, request: Request, user_pk: str) -> User | bool:
        user = request.user
        if user.pk == user_pk:
            return user
        return False

    def __get_file_path(self, request: Request, file_name: str) -> str:
        user = request.user
        try:
            image = Image.objects.get(original_image=f"{user.id}/images/{file_name}")
            file_path = os.path.join(
                os.path.dirname(image.original_image.path), file_name
            )
        except ObjectDoesNotExist:
            file_path = self.__find_other_matching_file(request, file_name)
        return file_path

    def __find_other_matching_file(self, request: Request, file_name: str) -> str:
        user = request.user
        images_dir = os.listdir(os.path.join(f"{os.getcwd()}/media/{user.id}/images/"))
        file_path = ""
        for img_file in images_dir:
            if img_file == file_name:
                file_path = os.path.join(
                    f"{os.getcwd()}/media/{user.id}/images/{img_file}"
                )
        return file_path

    def __handle_open_file(self, file_path: str) -> HttpResponse | Response:
        if os.path.exists(file_path):
            with open(file_path, "rb") as f:
                image_data = f.read()
                return HttpResponse(image_data, content_type="image/jpeg")
        return Response({"error": "Image not found"}, status=status.HTTP_404_NOT_FOUND)

    def get(self, request: Request, user_pk: str, file_name: str) -> Response:
        if not self.__authorize_user(request, user_pk):
            return Response(
                {"error": "You do not have access to this image"},
                status=status.HTTP_403_FORBIDDEN,
            )
        file_path = self.__get_file_path(request, file_name)
        return self.__handle_open_file(file_path)
