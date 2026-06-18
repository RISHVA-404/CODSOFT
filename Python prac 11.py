from PIL import Image

img = Image.open(r"C:\Users\NEAVISHRISHVA J\OneDrive\Documents\Arduino\Pictures\SCHOOL PHOTO.jpg")

print("Original Image")
img.show()

gray = img.convert("L")

resized = gray.resize((200, 200))

print("Processed Image")
resized.show()

resized.save("profile_output.jpg")

print("Image saved as profile_output.jpg")