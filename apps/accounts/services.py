from django.contrib.auth import get_user_model

User = get_user_model()

# ------ Serivce 1: Custome service to only create a new user and save it in the db
def register_user(email, username, password):
    """
    Service to handle user registration logic.
    """
    return User.objects.create_user(
        email=email,
        username=username,
        password=password
    )