from werkzeug.security import generate_password_hash

new_password = "ayanfe" # Replace with your actual new password
hashed_password = generate_password_hash(new_password)
print(hashed_password)