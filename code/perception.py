import numpy as np
import cv2

from code.rover_state import RoverState

def color_thresh(img, rgb_thresh_lower=(160, 160, 160), rgb_thresh_upper=(255, 255, 255)):
    """
    Identify pixels with the specified threshold
    Threshold of RGB > 160 does a nice job of identifying ground pixels only
    :param img: Input image in RGB
    :param rgb_thresh_lower: tuple R,G,B for lower bound
    :param rgb_thresh_upper: tuple R,G,B for upper bound
    :return: image with 1, with the current selection (>lower and <=upper)
    """
    color_select = np.zeros_like(img[:, :, 0])
    above_thresh_lower = (img[:, :, 0] > rgb_thresh_lower[0]) \
                         & (img[:, :, 1] > rgb_thresh_lower[1]) \
                         & (img[:, :, 2] > rgb_thresh_lower[2])

    above_thresh_upper = (img[:, :, 0] <= rgb_thresh_upper[0]) \
                         & (img[:, :, 1] <= rgb_thresh_upper[1]) \
                         & (img[:, :, 2] <= rgb_thresh_upper[2])

    above_thresh = above_thresh_lower & above_thresh_upper

    color_select[above_thresh] = 1
    return color_select

# Define a function to convert from image coords to rover coords
def rover_coords(binary_img):
    # Identify nonzero pixels
    ypos, xpos = binary_img.nonzero()
    # Calculate pixel positions with reference to the rover position being at the 
    # center bottom of the image.  
    x_pixel = -(ypos - binary_img.shape[0]).astype(np.float)
    y_pixel = -(xpos - binary_img.shape[1]/2 ).astype(np.float)
    return x_pixel, y_pixel


# Define a function to convert to radial coords in rover space
def to_polar_coords(x_pixel, y_pixel):
    # Convert (x_pixel, y_pixel) to (distance, angle) 
    # in polar coordinates in rover space
    # Calculate distance to each pixel
    dist = np.sqrt(x_pixel**2 + y_pixel**2)
    # Calculate angle away from vertical for each pixel
    angles = np.arctan2(y_pixel, x_pixel)
    return dist, angles

# Define a function to map rover space pixels to world space
def rotate_pix(xpix, ypix, yaw):
    # Convert yaw to radians
    yaw_rad = yaw * np.pi / 180
    xpix_rotated = (xpix * np.cos(yaw_rad)) - (ypix * np.sin(yaw_rad))
                            
    ypix_rotated = (xpix * np.sin(yaw_rad)) + (ypix * np.cos(yaw_rad))
    # Return the result  
    return xpix_rotated, ypix_rotated

def translate_pix(xpix_rot, ypix_rot, xpos, ypos, scale): 
    # Apply a scaling and a translation
    xpix_translated = (xpix_rot / scale) + xpos
    ypix_translated = (ypix_rot / scale) + ypos
    # Return the result  
    return xpix_translated, ypix_translated


# Define a function to apply rotation and translation (and clipping)
# Once you define the two functions above this function should work
def pix_to_world(xpix, ypix, xpos, ypos, yaw, world_size, scale):
    # Apply rotation
    xpix_rot, ypix_rot = rotate_pix(xpix, ypix, yaw)
    # Apply translation
    xpix_tran, ypix_tran = translate_pix(xpix_rot, ypix_rot, xpos, ypos, scale)
    # Perform rotation, translation and clipping all at once
    x_pix_world = np.clip(np.int_(xpix_tran), 0, world_size - 1)
    y_pix_world = np.clip(np.int_(ypix_tran), 0, world_size - 1)
    # Return the result
    return x_pix_world, y_pix_world

# Define a function to perform a perspective transform
def perspect_transform(img, src, dst):
           
    M = cv2.getPerspectiveTransform(src, dst)
    warped = cv2.warpPerspective(img, M, (img.shape[1], img.shape[0]))# keep same size as input image
    
    return warped


# Apply the above functions in succession and update the Rover state accordingly
def perception_step(Rover):
    """
    perception step
    :param RoverState Rover: the rover
    :return RoverState: updated rover
    """
    # Perform perception steps to update Rover()
    # TODO: 
    # NOTE: camera image is coming to you in Rover.img
    image = Rover.img
    # 1) Define source and destination points for perspective transform
    source = np.float32([[14, 140], [301, 140], [200, 96], [118, 96]])
    dest_half_size = 5
    dest_size = dest_half_size * 2
    dest_center_x = image.shape[1] / 2
    dest_start_y = image.shape[0] - 5

    destination = np.float32([[dest_center_x - dest_half_size, dest_start_y],
                     [dest_center_x + dest_half_size, dest_start_y],
                     [dest_center_x + dest_half_size, dest_start_y - dest_size],
                     [dest_center_x - dest_half_size, dest_start_y - dest_size]])
    # 2) Apply perspective transform
    warped = perspect_transform(image, source, destination)

    # 3) Apply color threshold to identify navigable terrain/obstacles/rock samples
    sand_selection = color_thresh(warped, rgb_thresh_lower=(160, 160, 160))
    rock_selection = color_thresh(warped, rgb_thresh_lower=(100, 0, 0), rgb_thresh_upper=(180, 180, 70))

    # 4) Update Rover.vision_image (this will be displayed on left side of screen)
    Rover.vision_image[:, :, 0] = sand_selection
    Rover.vision_image[:, :, 1] = rock_selection
#    Rover.vision_image[:, :, 2] = image

    # 5) Convert map image pixel values to rover-centric coords
    obstacle_xpix, obstacle_ypix = rover_coords(sand_selection)
    rock_xpix, rock_ypix = rover_coords(rock_selection)

    # 6) Convert rover-centric pixel values to world coordinates
    rover_xpos = Rover.pos[0]
    rover_ypos = Rover.pos[1]
    rover_yaw = Rover.yaw
    scale = 10   # ???
    obstacle_x_world, obstacle_y_world = pix_to_world(obstacle_xpix, obstacle_ypix, rover_xpos,
                                                      rover_ypos, rover_yaw,
                                                      Rover.worldmap.shape[0], scale)
    rock_x_world, rock_y_world = pix_to_world(rock_xpix, rock_ypix, rover_xpos,
                                              rover_ypos, rover_yaw,
                                              Rover.worldmap.shape[0], scale)

    # 7) Update Rover worldmap (to be displayed on right side of screen)
    Rover.worldmap[obstacle_y_world, obstacle_x_world, 0] += 1
    Rover.worldmap[rock_y_world, rock_x_world, 1] += 1
        #          Rover.worldmap[navigable_y_world, navigable_x_world, 2] += 1

    # 8) Convert rover-centric pixel positions to polar coordinates
    # Update Rover pixel distances and angles
        # Rover.nav_dists = rover_centric_pixel_distances
        # Rover.nav_angles = rover_centric_angles
    
 
    
    
    return Rover