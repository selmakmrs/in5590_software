# Assignment 6 - IN5590
<!-- replace heading to name of prototype/robot -->
Siver Meek Strand & Selma Karoline Matilde Ramber Storstad


## 1) Optimization
The optimization we performed for our robot focused on improving its ability to detect a person’s emotion. To achieve this, we used two different models, one for face detection and one for emotion classification.

For face detection, we used the YuNet model [^1].
This model is responsible for detecting the face used as input to the emotion classifier, and it also allows the robot to track faces in real time.

For emotion detection, we trained a YOLO-based model using the Ultralytics Python library. We used a dataset from Kaggle [^2], which contains images labeled with seven emotions: angry, disgust, fear, happy, neutral, sad, and surprise. After training, the model reached a top-1 accuracy of 0.7, and the confusion matrix looked promising.
[![Image of confusion matrix](./optimization\confusion_matrix_normalized.png)]

When using the model in a live camera feed, the quality of emotion recognition decreased, which was expected. Some emotions were very easy for the model to classify (e.g., happy and angry), while others were more difficult (e.g., sad and disgust). We also only wanted the robot to react when a person expressed the emotion clearly.

To handle these issues, we tested the model on the Raspberry Pi camera with five different people. Each person was asked to clearly display each emotion. We then recorded the confidence scores the model produced for the predicted emotion. Using these scores, we set a custom threshold for each emotion:
* Emotions like happy, angry, and surprised consistently produced high confidence values → higher thresholds.
* Emotions like sad and fear often produced lower scores → lower thresholds.

These thresholds determine whether the robot should trigger an emotional response. To avoid false positives, the robot only reacts when the same emotion is detected for at least three consecutive frames, and the confidence score is above the corresponding threshold.


## 2) Firmware/software for the robot/prototype

<!-- delete from here-->
There are 2 software parts to be delivered

All the software for the controller optimization, should be put into `./optimization/src`

All the software for getting your prototype to work, should be put into `./src`. 

If you use Python, set up a `requirement.txt` that includes all the necessary modules.
<!-- ....to here-->

Setup instructions optimization:
```
$ conda create --name <ENV_NAME> --file requirements.txt
$ conda activate <ENV_NAME>
```

Run instructions optimization: 
```
$ python 
```

Setup instructions robot:
```
$ conda create --name <ENV_NAME> --file requirements.txt
$ conda activate <ENV_NAME>
```

Run instructions robot: 
```
$ python 
```

<!-- delete from here-->
**Deliverables:** Source code in `./optimization/src` and `./src`, and setup/run instructions in this README.
<!-- ....to here-->

## 3) Images from testing the robot

<!-- delete from here-->
Take a photo of the robot/prototype in operation. Additionally, make a GIF that shows 
the robot moving.
<!-- ....to here-->

[![Image of the prototype in action](./poster/images/3.png)](./poster/main.pdf)

[![GIF of the prototype in action](./poster/images/3.gif)](./poster/main.pdf)

<!-- delete from here-->
**GIF instructions:** Make a GIF that shows the prototype working. The GIF should:

- Not be more than 10 seconds long.
- Not be more than 25MB.
- Be 1:1 ratio.

FFmpeg can help you with the enlisted requirements. Here is a starting point:

```
ffmpeg -i IMG_4730.MOV -t 10s -vf 'crop=600:600' -r 15  output/3.gif
```
**Deliverables:** Image and GIF showing the robot in action as `./poster/images/3.png` and `./poster/images/3.gif`.

## 4) Poster

Create a poster based on the template in `./poster/`. 
There are some instructions in `./poster/README.md` in how to use the poster template.

Make a QR code that links to this github repo. See tip in `./poster/README.md`

We will hang all the posters in the common area in ROBIN after the deadline.

**Deliverables:** A nicely formatted/camera ready poster as `./poster/main.pdf`. Include all `.tex`-files and images in `./poster/` and `./poster/images/` so the PDF is reproducable. 
<!-- ....to here-->

Read more on my poster about the robot [here](./poster/main.pdf). For information on
CAD files, go to [this repo](link to assignment 5).

<!-- Replace `(link to assignment 5)` with link to *your* assignment 5.-->

## 5) Prototyping process
<!-- delete from here-->
Describe at least three iterations/milestones during the process that was crucial to reaching the goals described in assignment 4. Include images/illustrations in each of them. Example:

### Iteration 1
- **Task/milestone:** Make a compliant mechanism for animatronics robot for rotating it's head.
- **Requirements:**
    - Be able to tilt it's head $30^\circ$ in roll, yaw and pitch. Ref IMAGE.
- **Implementation:** See solidworks drawing.
- **Testing:** In simulation, the mechanism worked as intended. However, when testing in real life the mechanism broke.
- **Evaluation:** Running FEM analysis on the links that broke gave us a starting point to improve the mechanism.
- **Plan:**
    - Run topology optimization on the most fragile components.
    - Experiment with different infill.
    - Use ball bearings instead of bushings in the joints.
  
### Iteration 2

...

### Iteration 3

...

<!-- ....to here-->
## 6) Future work

<!-- delete from here to end of file -->

In one paragraph, describe future work for your prototype. Moreover, describe what you would do different
if you started the process again.



## References

[^1]: (https://huggingface.co/spaces/sam749/YuNet-face-detection/blob/main/face_detection_yunet_2023mar.onnx)
[^2]: (https://www.kaggle.com/datasets/jonathanoheix/face-expression-recognition-dataset/data)