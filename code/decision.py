import numpy as np

def decision_step(Rover):
    """
    This is where you can build a decision tree for determining throttle, brake and steer
    commands based on the output of the perception_step() function
    :param RoverState Rover: the rover
    :return: the rover
    :rtype: RoverState
    """

    # Implement conditionals to decide what to do given perception data
    # Here you're all set up with some basic functionality but you'll need to
    # improve on this decision tree to do a good job of navigating autonomously!

    # Record position every second, for detecting when the rover is stuck
    current_second = int(Rover.total_time)
    array_index = current_second % Rover.pos_every_second.shape[0]
    Rover.pos_every_second[array_index, 0] = Rover.pos[0]
    Rover.pos_every_second[array_index, 1] = Rover.pos[1]
    Rover.pos_every_second[array_index, 2] = Rover.steer
    tolerance = 0.05

    is_stuck = (abs(Rover.pos_every_second[:, 0] - Rover.pos[0]) < tolerance).all() and \
        (abs(Rover.pos_every_second[:, 1] - Rover.pos[1]) < tolerance).all()
    if is_stuck:
        print("STUCK, trying to get rolling")
        Rover.throttle = np.min(np.random.random_integers(-1, 10), 0) / 5
        Rover.brake = 0
        Rover.steer = -15
        Rover.pos_every_second[array_index, 0] = -1  # Prevent being in the same condition after the turn
        Rover.mode = 'stop'
        return Rover
    is_around_steering = (Rover.pos_every_second[:, 2] == 15).all() or (Rover.pos_every_second[:, 2] == -15).all()
    if is_around_steering:
        print("Going in rounds, break it")
        Rover.steer = np.random.random_integers(-10, 10)
        return Rover

    if Rover.active_sample_position is not None and Rover.active_sample_start_time is not None:
        if Rover.active_sample_start_time + Rover.sample_search_timeout < Rover.total_time:
            # Giving up for this sample for now
            print("Stopping sample search. start {}, timeout {}, total time {}".format(
                Rover.active_sample_start_time, Rover.sample_search_timeout, Rover.total_time))
            Rover.mode = "stop"
            Rover.active_sample_position = None
            Rover.active_sample_start_time = None
            Rover.active_sample_search_ignore_until = Rover.total_time + Rover.active_sample_search_cooldown
            return Rover
        # Slowly steer to the sample
        active_sample_angle_degree = Rover.active_sample_angle * 180 / np.pi
        if active_sample_angle_degree < 0:
            active_sample_angle_degree += 360
        Rover.steer = np.clip(active_sample_angle_degree - Rover.yaw, -15, 15)
        print("************** TRYING TO GET TO THE SAMPLE.  Yaw {}, active_sample_angle {}, steer {}".format(
            Rover.yaw, active_sample_angle_degree, Rover.steer
        ))

        Rover.throttle = Rover.throttle_set * min(1, Rover.active_sample_distance)
        if np.abs(Rover.yaw - active_sample_angle_degree) > 140:
            Rover.throttle *= -1
        Rover.brake = max(1 - Rover.active_sample_distance, 0)

        if Rover.near_sample and Rover.vel == 0 and not Rover.picking_up:
            Rover.send_pickup = True

            Rover.mode = "stop"
            Rover.picked_up_sample_position.append(Rover.active_sample_position)
            Rover.active_sample_position = None
            Rover.active_sample_start_time = None
        return Rover

    # Check if we have vision data to make decisions with
    if Rover.nav_angles is not None:
        # Check for Rover.mode status
        if Rover.mode == 'forward': 
            # Check the extent of navigable terrain
            if len(Rover.nav_angles) >= Rover.stop_forward:  
                # If mode is forward, navigable terrain looks good 
                # and velocity is below max, then throttle 
                if Rover.vel < Rover.max_vel:
                    # Set throttle value to throttle setting
                    Rover.throttle = Rover.throttle_set
                else: # Else coast
                    Rover.throttle = 0
                Rover.brake = 0
                # Set steering to average angle clipped to the range +/- 15
                Rover.steer = np.clip(np.mean(Rover.nav_angles * 180/np.pi), -15, 15)
            # If there's a lack of navigable terrain pixels then go to 'stop' mode
            elif len(Rover.nav_angles) < Rover.stop_forward:
                    # Set mode to "stop" and hit the brakes!
                    Rover.throttle = 0
                    # Set brake to stored brake value
                    Rover.brake = Rover.brake_set
                    Rover.steer = 0
                    Rover.mode = 'stop'

        # If we're already in "stop" mode then make different decisions
        elif Rover.mode == 'stop':
            # If we're in stop mode but still moving keep braking
            if Rover.vel > 0.2:
                Rover.throttle = 0
                Rover.brake = Rover.brake_set
                Rover.steer = 0
            # If we're not moving (vel < 0.2) then do something else
            elif Rover.vel <= 0.2:
                # Now we're stopped and we have vision data to see if there's a path forward
                if len(Rover.nav_angles) < Rover.go_forward:
                    Rover.throttle = 0
                    # Release the brake to allow turning
                    Rover.brake = 0
                    # Turn range is +/- 15 degrees, when stopped the next line will induce 4-wheel turning
                    Rover.steer = -15 # Could be more clever here about which way to turn
                # If we're stopped but see sufficient navigable terrain in front then go!
                if len(Rover.nav_angles) >= Rover.go_forward:
                    # Set throttle back to stored value
                    Rover.throttle = Rover.throttle_set
                    # Release the brake
                    Rover.brake = 0
                    # Set steer to mean angle
                    Rover.steer = np.clip(np.mean(Rover.nav_angles * 180/np.pi), -15, 15)
                    Rover.mode = 'forward'
    # Just to make the rover do something 
    # even if no modifications have been made to the code
    else:
        Rover.throttle = Rover.throttle_set
        Rover.steer = 0
        Rover.brake = 0
        
    # If in a state where want to pickup a rock send pickup command
    if Rover.near_sample and Rover.vel == 0 and not Rover.picking_up:
        Rover.send_pickup = True
    
    return Rover

