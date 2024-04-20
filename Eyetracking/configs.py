# Define fundamental parameters for fixation detection
min_fixation_duration_sec = 0.15
frames_per_second = 30
min_fixation_frames = int(min_fixation_duration_sec * frames_per_second)
threshold_for_similarity = 0.04

# Specify dimensions for visual patches
patch_dimensions = (63, 111)  # width x height
field_of_view_degrees = (115, 90)  # horizontal x vertical field of view in degrees
fovea_fov = 13  # field of view for the fovea in degrees
near_peripheral_fov = 30  # physiological field of view for near periphery
mid_peripheral_fov = 60  # physiological field of view for mid periphery

# Color configuration for different visual areas
color_fovea = (255, 255, 0)
color_center = (255, 0, 0)
color_parafovea = (0, 255, 0)
color_periphery = (0, 0, 255)
color_mid_periphery = (0, 255, 255)

# Image configuration
image_dimensions = (400, 400, 3)  # width x height x color channels
image_width, image_height = image_dimensions[0], image_dimensions[1]
pixels_per_degree = (image_width / field_of_view_degrees[0], image_height / field_of_view_degrees[1])  # calculate pixels per degree for horizontal and vertical
