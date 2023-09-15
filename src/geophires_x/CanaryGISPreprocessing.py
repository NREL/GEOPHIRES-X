import arcpy
import shutil
import subprocess
import multiprocessing
import sys
import runpy
import os
from datetime import datetime

os.chdir("D:\\Work\\GEOPHIRES3-master")
arcpy.env.workspace = "D:/Work/ProjectCanary/GISData.gdb"
FootPrints = "D:/Work/ProjectCanary/GISData.gdb/PlantFootPrints"
fieldList = arcpy.ListFields(FootPrints)
NL="\n"
arcpy.env.overwriteOutput = True
now = datetime.now() # current date and time
date_time = now.strftime("%Y%m%d%H%M%S")

#Remove joins
#result=arcpy.management.RemoveJoin("r"D:\Work\ProjectCanary\GISData.gdb\PlantFootPrints", '')

#Calculate the area in sq km
result=arcpy.management.CalculateGeometryAttributes("r"D:\Work\ProjectCanary\GISData.gdb\PlantFootPrints", "Shape_Area_km2 AREA_GEODESIC", '', "SQUARE_KILOMETERS", 'PROJCS["World_Cylindrical_Equal_Area",GEOGCS["GCS_WGS_1984",DATUM["D_WGS_1984",SPHEROID["WGS_1984",6378137.0,298.257223563]],PRIMEM["Greenwich",0.0],UNIT["Degree",0.0174532925199433]],PROJECTION["Cylindrical_Equal_Area"],PARAMETER["False_Easting",0.0],PARAMETER["False_Northing",0.0],PARAMETER["Central_Meridian",0.0],PARAMETER["Standard_Parallel_1",0.0],UNIT["Meter",1.0]]', "SAME_AS_INPUT")

#use the temperature point data set to assign the average, min, and max temperature for the plant footprints
result=arcpy.analysis.SpatialJoin(r"D:\Work\ProjectCanary\GISData.gdb\PlantFootPrints", r"D:\Work\ProjectCanary\GISData.gdb\temperatures_2022_pt", r"D:\Work\ProjectCanary\GISData.gdb\PlantFootPrints_SpatialJoin", join_operation="JOIN_ONE_TO_ONE", join_type="KEEP_ALL", match_option="CLOSEST_GEODESIC", search_radius="10 DecimalDegrees")

#Crustal Type Processing
result=arcpy.analysis.PairwiseIntersect(r"D:\Work\ProjectCanary\GISData.gdb\Crustal_Type_py;PlantFootPrints_SpatialJoin", r"D:\Work\ProjectCanary\GISData.gdb\PlantFootPrints_AvgT_MinT_MaxT_CT_PT", "ALL", None, "INPUT")
result=arcpy.management.DeleteField(r"D:\Work\ProjectCanary\GISData.gdb\PlantFootPrints_AvgT_MinT_MaxT_CT_PT", "FID_Crustal_Type_py;DOMAIN;REGION;ACCR_AGE;NOTES;URL;FID_PlantFootPrints_SpatialJoin;Join_Count;TARGET_FID", "DELETE_FIELDS")

#cleanup and backup
result=arcpy.management.Rename(r"D:\Work\ProjectCanary\GISData.gdb\PlantFootPrints", r"D:\Work\ProjectCanary\GISData.gdb\PlantFootPrints" + date_time, "FeatureClass")
result=arcpy.management.Rename(r"D:\Work\ProjectCanary\GISData.gdb\PlantFootPrints_AvgT_MinT_MaxT_CT_PT", r"D:\Work\ProjectCanary\GISData.gdb\PlantFootPrints", "FeatureClass")
