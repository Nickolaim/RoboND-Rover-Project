## Project: Search and Sample Return
### Writeup Template: You can use this file as a template for your writeup if you want to submit it as a markdown file, but feel free to use some other method and submit a pdf if you prefer.

---


**The goals / steps of this project are the following:**  

**Training / Calibration**  

* Download the simulator and take data in "Training Mode"
* Test out the functions in the Jupyter Notebook provided
* Add functions to detect obstacles and samples of interest (golden rocks)
* Fill in the `process_image()` function with the appropriate image processing steps (perspective transform, color threshold etc.) to get from raw images to a map.  The `output_image` you create in this step should demonstrate that your mapping pipeline works.
* Use `moviepy` to process the images in your saved dataset with the `process_image()` function.  Include the video you produce as part of your submission.

**Autonomous Navigation / Mapping**

* Fill in the `perception_step()` function within the `perception.py` script with the appropriate image processing functions to create a map and update `Rover()` data (similar to what you did with `process_image()` in the notebook). 
* Fill in the `decision_step()` function within the `decision.py` script with conditional statements that take into consideration the outputs of the `perception_step()` in deciding how to issue throttle, brake and steering commands. 
* Iterate on your perception and decision function until your rover does a reasonable (need to define metric) job of navigating and mapping.  

[//]: # (Image References)

[image1]: ./output/rock_orig.png
[image2]: ./output/rock_navigable.png
[image3]: ./output/rock_obstacle.png
[image4]: ./output/rock_sample.png
[image5]: ./output/test_mapping.mp4 
[image6]: ./output/fidelity_render_complete.png

## [Rubric](https://review.udacity.com/#!/rubrics/916/view) Points
### Here I will consider the rubric points individually and describe how I addressed each point in my implementation.  

---
### Writeup / README

#### 1. Provide a Writeup / README that includes all the rubric points and how you addressed each one.  You can submit your writeup as markdown or pdf.  

You're reading it!

### Notebook Analysis
#### 1. Run the functions provided in the notebook on test images (first with the test data provided, next on data you have recorded). Add/modify functions to allow for color selection of obstacles and rock samples.

Here is an original image

![original][image1]

Navigatable

![navigatable][image2]


Sample

![navigatable][image4]


Obstacle

![navigatable][image3]


Note, that the same filtering technique used on the transformed images, but I found doing filtering on them not as good visually as filtering original images. 


#### 1. Populate the `process_image()` function with the appropriate analysis steps to map pixels identifying navigable terrain, obstacles and rock samples into a worldmap.  Run `process_image()` on your test data using the `moviepy` functions provided to create video output of your result. 
Video is in the `./output` folder or at the link below 

![Generated video][image5]
### Autonomous Navigation and Mapping

#### 1. Fill in the `perception_step()` (at the bottom of the `perception.py` script) and `decision_step()` (in `decision.py`) functions in the autonomous mapping scripts and an explanation is provided in the writeup of how and why these functions were modified as they were.

*Navigation*

Steps 1-8 are taken from the lessons, with minor modifications.  The only thing I believe was not in the lessons is the code for detecting samples, but it is very similar to the other code

I added step 9 to calculate distance and direction from rover to the sample. It is needed during navigation for picking up the sample 

*Decision*

In addition to the basic decision logic I've added:

- Samples search. If a sample is detected within 10 meters of the rover:
    - stop the rover
    - slowly navigate in the direction of the sample, keeping velocity low
    - when very close to the sample, start applying the break
    - if cannot get the sample in sample_search_timeout seconds, give up, and resume basic navigation
    - after giving up do not pickup any sample, unless active_sample_search_cooldown seconds pass
- Stuck detection and prevention
    - record the rover position for the last seconds_for_being_stuck. If it is within small range, consider rover stuck, and try to get it going by steering
- Detection and prevention for going in circle
    - similar to stuck detection, except that the thing that is being monitored is steering angle. If it is the same during seconds_for_being_stuck, change steering angle to a random value in a certain range.

#### 2. Launching in autonomous mode your rover can navigate and map autonomously.  Explain your results and how you might improve them in your writeup.  

**Note: running the simulator with different choices of resolution and graphics quality may produce different results, particularly on different machines!  Make a note of your simulator settings (resolution and graphics quality set on launch) and frames per second (FPS output to terminal by `drive_rover.py`) in your writeup when you submit the project so your reviewer can reproduce your results.**

I used 1400x1050 resolution with Good quality, output showed 16 FPS

I cropped the output after processing. It seemed to me that fidelity was not good because of how far pixels were processed, so I just got read of them

I am not sure that map for where rover can operate can be composed accurately by just processing the colors. There are some places where rover still can move on the mountains, but it is not considered movable.  
I generate a fidelity map while navigating, and it looks like the current approach works badly on borders (or the truth_map is not accurate)  

![fidelity map][image6]


*Other things that are implemented*
- Output map and the camera image in PNG (JPEG was blurry)
- Display the rover on the map
- Generate the fidelity map as .png in /output folder to see how detection is working

All 3 things were useful for me for better understanding what's happening, consider adding them to the next program.

*Not done*
- Return to the center of the map when all samples are gathered.  Super simple code for this would be to:
  - On start, remember the location, and expand it to some rectangle
  - When all 6 samples are gathered, switch to 'Navigate to center mode'
  - Continue randomly moving, until rover is in the start rectangle


There are certain things that can be improved. Now the current way is more ad-hock and pretty messy. It should be restructured with the implementation of commands, like "stop", "navigate to X,Y with speed Z", "rotate by 180 degree", and so on, and the basic algorithm should use this commands.

I like the code for getting rover unstuck. It mostly works and can keep rover running for a long time.
