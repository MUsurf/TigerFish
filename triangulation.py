import math

class Triangulation: 
    def triangulate(cam1X, cam2X, cam1Y, cam2Y):
        # finds the bottom angles of the triangle
        cam1xangle = 90-abs(cam1X)
        cam2xangle = 90-abs(cam2X)
        cam1yangle = 90-abs(cam1Y)
        cam2yangle = 90-abs(cam2Y)

        #calculates the angle on the top of the triangle
        topAngleX = 180-cam1xangle-cam2xangle
        topAngleY = 180-cam1yangle-cam2yangle
        
        
        
        #calculates the x-distance from each camera to the object using the law of sines
        if cam1xangle+cam2xangle >= 180:
            Cam1xdistance = 0
            Cam2xdistance = 0
        else:
            Cam1xdistance = (1/(math.sin(math.radians(topAngleX))))*(math.sin(math.radians(cam1xangle)))
            Cam2xdistance = (1/(math.sin(math.radians(topAngleX))))*(math.sin(math.radians(cam2xangle)))
            
        
        #calculates the y-distance from each camera to the object
        print(cam1yangle)
        print(cam2yangle)
        print (math.sin(math.radians(cam1yangle))+ math.sin(math.radians(cam2yangle)))
        if cam1yangle+cam2yangle >= 180:
            Cam1ydistance = 0
            Cam2ydistance = 0
        else:
            Cam1ydistance = (1/(math.sin(math.radians(topAngleY))))*(math.sin(math.radians(cam1yangle)))
            Cam2ydistance = (1/(math.sin(math.radians(topAngleY))))*(math.sin(math.radians(cam2yangle)))
        print(Cam1ydistance)
        print(Cam2ydistance)
        #finds the length of the distance from the object to the origin
        Cam1Distance = math.sqrt((Cam1xdistance**2)+(Cam1ydistance**2))
        Cam2Distance = math.sqrt((Cam2xdistance**2)+(Cam2ydistance**2))
        print(Cam1Distance)
        print(Cam2Distance)
        
        # converts to x y z coordinates
        Cam1Xcoord = Cam1xdistance*math.cos(math.radians(cam1Y))
        Cam1Ycoord = Cam1xdistance*math.sin(math.radians(cam1Y))
        Cam1Zcoord = Cam1ydistance

        Cam2Xcoord = Cam2xdistance*math.cos(math.radians(cam2Y))
        Cam2Ycoord = Cam2xdistance*math.sin(math.radians(cam2Y))
        Cam2Zcoord = Cam2ydistance
        
        # averages the two camera coordinates to get a more accurate reading
        Xcoord = (Cam1Xcoord+Cam2Xcoord)/2
        Ycoord = (Cam1Ycoord+Cam2Ycoord)/2
        Zcoord = (Cam1Zcoord+Cam2Zcoord)/2
        return (Xcoord, Ycoord, Zcoord)
print(Triangulation.triangulate(20, 10, -30, 0))
print(math.sqrt(2.546245**2))