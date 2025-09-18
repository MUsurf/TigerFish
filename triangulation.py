import math

#Welcome to triangulation.py!!
#important things to note:
#assume cameras are 1 unit apart
#assume cameras are facing towards the positive y direction


def find3DVector(xAngle, zAngle):
    vector = [0, 1, 0]
    #find the vector after rotating x degrees down from the y axis
    vector[0] = math.cos(math.radians(90-xAngle))
    vector[1] = vector[1]*math.sin(math.radians(90-xAngle))
    
    #find the vector after rotating z degrees around the y axis
    vector[0] = vector[0]*math.cos(math.radians(zAngle))
    vector[1] = vector[1]*math.cos(math.radians(zAngle))
    vector[2] = math.sin(math.radians(zAngle))
    return vector


class Triangulation: 
    def triangulate(cam1X, cam2X, cam1Z, cam2Z):
        # finds the bottom angles of the triangle
        cam1xangle = 90-abs(cam1X)
        cam2xangle = 90-abs(cam2X)
        cam1zangle = 90-abs(cam1Z)
        cam2zangle = 90-abs(cam2Z)
    

        #calculates the angle on the top of the triangle
        topAngleX = 180-cam1xangle-cam2xangle
        topAngleY = 180-cam1zangle-cam2zangle
        
        
        #calculates the x-distance from each camera to the object using the law of sines
        if cam1xangle+cam2xangle >= 180:
            Cam1xdistance = 0
            Cam2xdistance = 0
        else:
            Cam1xdistance = (1/(math.sin(math.radians(topAngleX))))*(math.sin(math.radians(cam1xangle)))
            Cam2xdistance = (1/(math.sin(math.radians(topAngleX))))*(math.sin(math.radians(cam2xangle)))
            
        
        #calculates the y-distance from each camera to the object
        #print(cam1yangle)
        #print(cam2yangle)
        if cam1zangle+cam2zangle >= 180:
            Cam1ydistance = 0
            Cam2ydistance = 0
        else:
            Cam1zdistance = (1/(math.sin(math.radians(topAngleY))))*(math.sin(math.radians(cam1zangle)))
            Cam2zdistance = (1/(math.sin(math.radians(topAngleY))))*(math.sin(math.radians(cam2zangle)))
        
        #testing prints
        print("Cam1xdistance:", Cam1xdistance)
        print("Cam2xdistance:", Cam2xdistance)

        print("Cam1zdistance:", Cam1zdistance)
        print("Cam2zdistance:", Cam2zdistance)

        #finds the length of the distance from the object to the origin
        #to do this, I use the pythagorean theorem
        #I don't know if this works, but I'm trying it
        Cam1Distance = math.sqrt((Cam1xdistance**2)+(Cam1zdistance**2))
        Cam2Distance = math.sqrt((Cam2xdistance**2)+(Cam2zdistance**2))
        print("distance Cam1:", Cam1Distance)
        print("distance Cam2:", Cam2Distance)

        #finds the 3D vector from each camera to the object
        cam1Vector = [v * Cam1Distance for v in find3DVector(cam1X, cam1Z)]
        cam2Vector = [v * Cam2Distance for v in find3DVector(cam2X, cam2Z)]

        #Only returns the vector from camera 1
        return (cam1Vector)
