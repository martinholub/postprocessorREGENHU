#!/usr/bin/env python
import fileinput
import re
import sys
#########################################
# Must change file name to correspond to your file
# Afterwards run the script via (I)Python shell 'run posprocessorREGENHU.py'
###################################################
# Custom settings:
extrusionSpeed = 'F800'
startDelay = 'F0.260'
inFileName = 'SiliconeEar_133p5.iso' 

####################################################
# inFileName = sys.argv[1]
# outFileName = sys.argv[2] 
inFile = open(inFileName, 'r')
outbuffer = ""

#######################################################
# Regex 
undesiredGcodePattern = re.compile(r'(M106|M107|M126|M127|G21 ; set units to millimeters|G90 ; use absolute coordinates|M83 ; use relative distances for extrusion).*') #106 S127

# Useless Patterns
# Note that speed is hardocoded for each extrudeMovePattern !!
undesiredPatternSpeed = re.compile(r'E[0-9]\.[0-9]+ F799.998$')
undesiredPatternExtrude = re.compile(r'E[0-9]\.[0-9]+')

# Travel Move Pattern
travelMovePattern = re.compile(r'^G1 ([XYZ][-0-9]+\.[0-9]+.){1,3}(F[0-9]+\.[0-9]+.)$')

#Extrude Move Pattern
extrudeMovePattern = re.compile(r'^G1 ([XYZ][-0-9]+\.[0-9]+.){1,3}(E[0-9]+\.[0-9]+.)(F[0-9]+\.[0-9]+.)$')

getXPositionPattern = re.compile(r'[Xx]-*\d*\.\d*') #Get X coordinates for this line, used to find last known position 
getYPositionPattern = re.compile(r'[Yy]-*\d*\.\d*') #Get Y coordinates for this line, used to find last known position 
getZPositionPattern = re.compile(r'[Zz]-*\d*\.\d*') #Get Z coordinates for this line, used to find last known position 
endOfFilePattern = re.compile(r';END')

xPositionGlobal = float(0)
yPositionGlobal = float(0)
zPositionGlobal = float(0)


previousLine = ""
currentTool = 0
extruding = True
count = 0;

############################################################
def updatePosition(line):
	global xPositionGlobal, yPositionGlobal, zPositionGlobal, lastKnownPosition
	xPos = xPositionGlobal
	yPos = yPositionGlobal
	zPos = zPositionGlobal
	xMatch = re.search(getXPositionPattern,line)
	if xMatch:
		xPos = float(xMatch.group(0)[1:])
	yMatch = re.search(getYPositionPattern,line)
	if yMatch:
		yPos = float(yMatch.group(0)[1:])
	zMatch = re.search(getZPositionPattern,line)
	if zMatch:
		zPos = float(zMatch.group(0)[1:])
	
	
	xPositionGlobal = xPos
	yPositionGlobal = yPos
	zPositionGlobal = zPos
	lastKnownPosition = ("G0 X"+str(xPos)+" Y"+str(yPos)+"\n")
	return lastKnownPosition

liftCode = """
;Lift the toolhead
G91
G0 Z5
G90
"""
lowerCode = """
;Lower the toolhead
G91
G0 Z-5
G90
"""
lastKnownPosition = "G0 X0 Y0 Z40\n"

#########################################################
print("Running the Postprocessor")

outbuffer += ";Post processed and modified for REGENHu BioFactory with ViscoTecPen \n"

for line in inFile:
	if re.match(endOfFilePattern,line):
		break
	# MH-20170517-Comment out global vairable assignement
	# global extruding, currentTool
	# http://stackoverflow.com/questions/20784758/global-variable-warning-in-python
	
	if re.search(undesiredGcodePattern,line):
		print("Discarded one line")
		pass
	#Will not discard entire line, now we need to check if it is a tool change
	
	elif (re.match(travelMovePattern,line)):
		
		if extruding:
			print("TRAVEL")
			outbuffer+="M96\n" # turns of extrusion
		lastKnownPosition = updatePosition(line)
		extruding = False
		outbuffer+=line
	elif (re.match(extrudeMovePattern, line)):

		if not extruding:
			print("PRINT")
			outbuffer+="M97\n" # turns on extrusion
			#Dwell?
			if count == 0 :
				outbuffer+="G04 "+ startDelay +" ;dwell for xzy ms\n" + extrusionSpeed + " "
				# Add startup Delay
			else :
				# Here one can add delay also after each turn off/on of extrusion
				outbuffer+=";G04 F0.100 ;dwell for xzy ms\n" + extrusionSpeed + " "
			count += 1
			
		lastKnownPosition = updatePosition(line)
		extruding = True
		# Remove some unnecessary code
		outbuffer+=re.sub(undesiredPatternSpeed, '', line)
	else:
		# Remove all other unnecessary code
		outbuffer+=re.sub(undesiredPatternExtrude, '', line)

outbuffer += ";Post processed and modified for REGENHu BioFactory with ViscoTecPen"
#close input
inFile.close()
#dump all to outfile
outFile = open(inFileName, 'w') 
print("Saving gcode to file")
outFile.write(outbuffer)
#close output
outFile.close()
print("Postprocessing done!")
