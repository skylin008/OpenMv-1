import sensor, image, time, lcd, math

lcd.init()
sensor.reset()
sensor.set_pixformat(sensor.RGB565)
sensor.set_framesize(sensor.QVGA)

sensor.set_contrast(-2)
sensor.set_gainceiling(16)
sensor.set_vflip(False)
sensor.set_hmirror(False)
sensor.set_auto_gain(False)
sensor.set_auto_whitebal(False)
IMG_HEIGHT = 224
IMG_WIDTH = 224
sensor.set_windowing((IMG_HEIGHT, IMG_WIDTH))

sensor.run(1)
sensor.skip_frames(time = 500)

COLOR_THRESHOLD = [(96, 100, -128, 127, -128, 127)]
AREA_THRESHOLD = 40
PIXELS_THRESHOLD = 40
LANE_ROI = (0, 112, IMG_WIDTH, 112)
BINARY_VIEW = True

MAG_THRESHOLD = 0
MIXING_RATE = 0.9

THROTTLE_OFFSET = 1000.0
THROTTLE_GAIN = 1.0
THROTTLE_INTEGRAL_MAX = 0.0
THROTTLE_INTEGRAL_MIN = 0.0
THROTTLE_PROPORTIONAL_GAIN = 1.0
THROTTLE_INTEGRAL_GAIN = 0.0
THROTTLE_DERIVATIVE_GAIN = 0.0
THROTTLE_CUT_OFF_ANGLE = 1.0
THROTTLE_CUT_OFF_RATE = 0.5

STEERING_OFFSET = 90
STEERING_INTEGRAL_MAX = -0.0
STEERING_INTEGRAL_MIN = 0.0
STEERING_PROPORTIONAL_GAIN = -20.0
STEERING_INTEGRAL_GAIN = 0.0
STEERING_DERIVATIVE_GAIN = -16

previousMillis = time.ticks_ms()

oldThrottle = None
throttleIntegral = 0
throttleResult = THROTTLE_OFFSET

oldSteering = None
steeringIntegral = 0
steeringResult = STEERING_OFFSET

# t_power = math.log(THROTTLE_CUT_OFF_RATE) / math.log(math.cos(math.radians(THROTTLE_CUT_OFF_ANGLE)))

# old_cx_normal = None
# def figure_out_steering(line):
#     global old_cx_normal

#     cy = IMG_HEIGHT / 2 / 2
#     cx = (line.rho() - (cy * math.sin(math.radians(line.theta())))) / math.cos(math.radians(line.theta()))

#     cx_middle = cx - (IMG_WIDTH / 2)
#     cx_normal = cx_middle / (IMG_WIDTH / 2)

#     if old_cx_normal != None:
#         old_cx_normal = (cx_normal * MIXING_RATE) + (old_cx_normal * (1.0 - MIXING_RATE))
#     else:
#         old_cx_normal = cx_normal

#     return old_cx_normal

# def figure_out_steering_v2(line):
#     x1,y1,x2,y2 = line[:4]
#     angle = 180/math.pi * math.atan((y2-y1)/(x2-x1))
#     xOffset = (x1 + x2) / 2 - IMG_WIDTH / 2
#     return(angle, xOffset)

# def figure_out_steering_v3(line):
#     angle = line.theta()
#     return angle

# def figure_out_steering_v4(line):
#     cy = IMG_HEIGHT / 2 / 2
#     cx = (line.rho() - (cy * math.sin(math.radians(line.theta())))) / math.cos(math.radians(line.theta()))

#     cx_middle = cx - (IMG_WIDTH / 2)
#     cx_normal = cx_middle / (IMG_WIDTH / 2)

#     return cx_normal

# # def figure_out_throttle(steering):
# #     t_result = math.pow(math.sin(math.radians(max(min(steering, 179.99), 0.0))), t_power)
# #     print(t_result, t_power, THROTTLE_GAIN, THROTTLE_OFFSET)
# #     return (t_result * THROTTLE_GAIN) + THROTTLE_OFFSET

old_cx_normal = None
def figure_out_steering(line):
    global old_cx_normal

    cy = IMG_HEIGHT / 4
    cx = (line.rho() - (cy * math.sin(math.radians(line.theta())))) / math.cos(math.radians(line.theta()))

    cx_middle = cx - (IMG_WIDTH / 2)
    cx_normal = cx_middle / (IMG_WIDTH / 2)

    if old_cx_normal != None: old_cx_normal = (cx_normal * MIXING_RATE) + (old_cx_normal * (1.0 - MIXING_RATE))
    else: old_cx_normal = cx_normal
    return old_cx_normal

t_power = math.log(THROTTLE_CUT_OFF_RATE) / math.log(math.cos(math.radians(THROTTLE_CUT_OFF_ANGLE)))


def figure_out_throttle(steering):
    t_result = math.pow(math.sin(math.radians(max(min(steering, 179.99), 0.0))), t_power)
    return t_result * THROTTLE_OFFSET

while True:
    time.clock().tick()
    img = sensor.snapshot().histeq()

    line = img.get_regression((COLOR_THRESHOLD), pixels_threshold = PIXELS_THRESHOLD, area_threshold = AREA_THRESHOLD, robust = True, roi = LANE_ROI)

    if line and line.magnitude() >= MAG_THRESHOLD:
        currentMillis = time.ticks_ms()
        millisDiff = time.ticks_diff(previousMillis, currentMillis)
        previousMillis = currentMillis


        # angle, xOffset = figure_out_steering_v2(line)
        # thetha = figure_out_steering_v3(line)
        # print(angle, thetha)
        newSteering = figure_out_steering(line)
        if oldSteering != None:
            steeringDiff = (newSteering - oldSteering)
        else:
            steeringDiff = 0
        oldSteering = newSteering

        steeringProportional = newSteering
        steeringIntegral = max(min(steeringIntegral + newSteering, STEERING_INTEGRAL_MAX), STEERING_INTEGRAL_MIN)
        if millisDiff:
            steeringDerivative = steeringDiff * 1000 / millisDiff
        else:
            steeringDerivative = 0
        steeringByPID = (STEERING_PROPORTIONAL_GAIN * steeringProportional) + (STEERING_INTEGRAL_GAIN * steeringIntegral) + (STEERING_DERIVATIVE_GAIN * steeringDerivative)

        steeringResult = STEERING_OFFSET + max(min(round(steeringByPID), 180 - STEERING_OFFSET), STEERING_OFFSET - 180)

        ##########################################

        # Hitta pw du vill ha, 1024 vid steering result = 90,
        # newThrottle = figure_out_throttle(steeringResult)

        # if oldThrottle != None:
        #     throttleDiff = newThrottle - oldThrottle
        # else:
        #     throttleDiff = 0
        # oldThrottle = newThrottle

        # throttleProportional = newThrottle
        # throttleIntegral = max(min(throttleIntegral + newThrottle, THROTTLE_INTEGRAL_MAX), THROTTLE_INTEGRAL_MIN)
        # if millisDiff:
        #     throttleDerivative = throttleDiff * 1000 / millisDiff
        # else:
        #     throttleDerivative = 0
        # throttleByPID = (THROTTLE_PROPORTIONAL_GAIN * throttleProportional) + (THROTTLE_INTEGRAL_GAIN * throttleIntegral) + (THROTTLE_DERIVATIVE_GAIN * throttleDerivative)

        # throttleResult = max(min(round(throttleByPID), 1000), 0)

        newThrottle = figure_out_throttle(steeringResult)

        if oldThrottle != None:
            throttleDiff = newThrottle - oldThrottle
        else:
            throttleDiff = 0
        oldThrottle = newThrottle

        throttleProportional = newThrottle
        throttleIntegral = max(min(throttleIntegral + newThrottle, THROTTLE_INTEGRAL_MAX), THROTTLE_INTEGRAL_MIN)
        if millisDiff:
            throttleDerivative = throttleDiff * 1000 / millisDiff
        else:
            throttleDerivative = 0
        throttleByPID = (THROTTLE_PROPORTIONAL_GAIN * throttleProportional) + (THROTTLE_INTEGRAL_GAIN * throttleIntegral) + (THROTTLE_DERIVATIVE_GAIN * throttleDerivative)

        throttleResult = max(min(round(throttleByPID), 1000), 0) / 1000

        # print(int((line.line()[0]+line.line()[2])/2),0,line.line()[2],line.line()[3])
        # print(line.line()[0],line.line()[1],line.line()[2],line.line()[3])
        # img.draw_line((int((line.line()[0]+line.line()[2])/2),0,line.line()[2],line.line()[3]), color=(0, 255, 0), thickness=2)
        img.draw_line(line.line(), color=(0, 255, 0), thickness=2)
        # printString = "a:%d, xO:%d" % (angle, xOffset)
        printString = "T:%d, S:%d t:%d, r:%d" % (throttleResult , steeringResult, line.theta(), line.rho())
    else:
        printString = "T:%d, S:%d" % (throttleResult , steeringResult)


    # Lägg till LegoAI här
    # gubbens y värde bestämmer bilens hastighet, sakta in destu högre y värde, alltså destu längre ner gubben är, ju närmre gubben är, gubbens storlek
    # gubbens x värde bestämmer hur bilen ska hålla sig till vägen
    # kanske x värdet på gubben borde ändra x värdet på linjen
    # kanske x värdet på gubben borde ändra vinkeln på linjen

    if BINARY_VIEW:
        img = img.binary(COLOR_THRESHOLD)
        if line:
            img.draw_line(line.line(), color=(0, 255, 0), thickness=2)

    img.draw_string(2, 2, printString, color=(0, 255, 0), scale=1)
    print(printString)

    lcd.display(img)
lcd.clear()
