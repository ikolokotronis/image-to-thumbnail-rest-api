<div id="top"></div>

<h3 align="center">image-to-thumbnail-rest-api</h1>

<details>
  <summary>Table of Contents</summary>
  <ol>
    <li>
      <a href="#getting-started">Getting Started</a>
    </li>
    <li><a href="#endpoints">Endpoints</a></li>
    <li><a href="#testing-user">Testing</a></li>
  </ol>
</details>

### Getting Started

1. Clone the repo
  ```
  git clone https://github.com/ikolokotronis/image-to-thumbnail-rest-api.git
  ```
2. Move to docker directory (assuming you are located in the project's root directory)
  ```
  cd ./image_to_thumbnail_rest_api/.docker/
  ```
3. Build the container
  ```
  docker compose up --build
  ```
4. Now you can access the API at http://127.0.0.1:8080

## Endpoints

In order to send valid requests, user needs to be authenticated. To achieve that, use the <a href="#login">login endpoint</a>.  
  
### Media access endponts

#### Standard Images
GET `media/<int:user_pk>/images/<str:file_name>`

#### Expiring Images
GET `media/expiring-images/<str:file_name>`

<br/>

### Authentication / Logging in
<div id="login"></div>

```
POST /users/login/
```
To log in, you can use the built-in <a href="#testing">testing account</a>.  
Request body example:

```
{
  "username": "admin",
  "password": "admin"
}
```

After receiving response, copy the <b>csrftoken</b> cookie from response headers and include that in your request headers as a value for <b>X-CSRFToken</b> field.


### Getting all images
`GET /images/`
<br/>
<br/>
Only images added by the request user are available for him.

Response example:
```
[
    {
        "pk": 27,
        "original_image": "/media/1/images/test.jpg",
        "created_at": "2022-06-21T23:21:22.467379Z"
    },
    {
        "pk": 28,
        "original_image": "/media/1/images/test_UkadI7r.jpg",
        "created_at": "2022-06-23T12:35:44.317739Z"
    },
    {
        "pk": 29,
        "original_image": "/media/1/images/test_W0gfr22.jpg",
        "created_at": "2022-06-23T13:00:54.707904Z"
    }
]
```

<br/>

### Uploading images
`POST /images/`
<br/>
<br/>
Uploading images require a `original_image` field to be included in the body.  As a value, it expects an image file in png or jpg format.  
Any other values will be rejected.  
#### Important note:
If user's tier plan comes with ability to fetch expiring links, there shoud also be a `live_time` field in the body, 
determining the amount of seconds the link will be available before it expires. Number range should be between `300` and `30000`.  
  
Request body example (assuming user tier is Enterprise):

```
{
  "original_image": test.jpg,
  "live_time": "500"
}
```
Response differs depending on which tier user currently has.  
Response example (assuming user tier is Enterprise):  
```
{
    "400px_thumbnail": "/media/1/images/test_ioN602N_400px_thumbnail.jpg",
    "200px_thumbnail": "/media/1/images/test_ioN602N_200px_thumbnail.jpg",
    "original_image": "/media/1/images/test_ioN602N.jpg",
    "500s_expiring_link": "/media/expiring-images/test_ioN602N.jpg",
    "success": "Image uploaded successfully"
}
```

### Testing
Because the API has no registration functionality, a testing admin user is created upon every container build, to allow accessing the django-admin panel.   
To access the account, use these credentials:  
* <b>username</b>: admin  
* <b>password</b>: admin  
  
Admin's default tier is <b>Enterprise</b>.  

<p align="right">(<a href="#top">back to top</a>)</p>
