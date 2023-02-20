from django.urls import reverse
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.test import APITestCase
from django.core.files.uploadedfile import SimpleUploadedFile

from images.models import Image
from users.models import User, Tier


class ImageTests(APITestCase):
    def setUp(self):
        """
        Create a premium user and 2 images for that user
        """
        tier = Tier.objects.create(
            name="Premium",
            presence_of_original_file_link=True,
            ability_to_fetch_expiring_link=False,
        )
        user = User.objects.create_user(username="some_name", password="some_password", tier=tier)
        self.client.post('/users/login/', {'username': 'some_name', 'password': 'some_password'})
        image = SimpleUploadedFile(
            name="test_image.jpg",
            content=open("tests/img/test.jpg", "rb").read(),
            content_type="image/jpg",
        )
        image2 = SimpleUploadedFile(
            name="test_image2.jpg",
            content=open("tests/img/test2.jpg", "rb").read(),
            content_type="image/jpg",
        )
        Image.objects.create(original_image=image, user=user)
        Image.objects.create(original_image=image2, user=user)

    def test_get_all_images(self):
        """
        Test that all images are returned
        """
        url = reverse("image-view")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            Image.objects.count(), 2
        )  # 2 images from setUp that are owned by test user
        self.assertEqual(len(response.data), 2)

    # def test_get_one_image(self):
    #     """
    #     Test that one image is returned
    #     """
    #     response = self.client.post('/users/login/', {'username': 'some_name', 'password': 'some_password'})
    #     request = response.wsgi_request
    #     url = f"{Image.objects.filter(user=request.user).first().original_image.url}/"  # get first image from setUp
    #     print(url)
    #     response = self.client.get(url)
    #     self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_upload_image(self):
        """
        Test that image is uploaded stored in database
        """
        url = reverse("image-view")
        image = SimpleUploadedFile(
            name="test_image.jpg",
            content=open("tests/img/test2.jpg", "rb").read(),
            content_type="image/jpg",
        )
        data = {"original_image": image}
        response = self.client.post(url, data, format="multipart")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(len(response.data), 4)  # 4 fields in response
        self.assertEqual(Image.objects.count(), 3)  # 2 images from setUp and 1 new one
        self.assertEqual(
            response.data["original_image"],
            f"{Image.objects.last().original_image.url}",
        )

    def test_upload_image_without_data(self):
        """
        Test that image is not uploaded if original_image is not provided
        """
        url = reverse("image-view")
        data = {}
        response = self.client.post(url, data, format="multipart")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(Image.objects.count(), 2)  # still just 2 images from setUp

    def test_upload_image_with_invalid_image_value(self):
        """
        Test that image is not uploaded if original_image value is not an image
        """
        url = reverse("image-view")
        data = {"original_image": "invalid_value"}
        response = self.client.post(
            url, data, format="multipart"
        )  # sending string instead of file
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(Image.objects.count(), 2)  # still just 2 images from setUp

    def test_upload_image_with_invalid_image_type(self):
        """
        Test by sending image with invalid type (not jpg/png)
        """
        url = reverse("image-view")
        data = {
            "original_image": SimpleUploadedFile(
                name="bmp-test.bmp",
                content=open("tests/img/bmp-test.bmp", "rb").read(),
                content_type="image/bmp",
            )
        }
        response = self.client.post(url, data, format="multipart")
        self.assertEqual(
            response.status_code, status.HTTP_400_BAD_REQUEST
        )  # sending bmp file
        self.assertEqual(Image.objects.count(), 2)
        self.assertEqual(response.data["error"], "Image format not supported")
