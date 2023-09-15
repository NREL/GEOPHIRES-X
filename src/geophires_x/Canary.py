import arcpy
import shutil
import subprocess
import multiprocessing
import sys
import runpy
import os

os.chdir("D:\\Work\\GEOPHIRES3-master")
arcpy.env.workspace = "D:/Work/ProjectCanary/GISData.gdb"
FootPrints = "D:/Work/ProjectCanary/GISData.gdb/PlantFootPrints"
fieldList = arcpy.ListFields(FootPrints)
NL="\n"

#iterate thru all the features
with arcpy.da.SearchCursor(FootPrints,['SHAPE@','Shape_Area_km2', "Shape_Thickness_km", "gppd_idnr", "tavg", "tmin", "tmax"]) as cursor:
    for row in cursor:
        shape=row[0]
        area = row[1]
        thick=row[2]
        id = row[3]
        tavg = row[4]
        tmin = row[5]
        tmax = row[6]
# open the outputfile, naming it based on the unique ID then write the values into it.
        with open("D:\\Work\\ProjectCanary\\"+id+".txt","w", encoding="UTF-8") as f:
            f.write("Reservoir Area, " + str(area) + NL)
            f.write("Reservoir Thickness, " + str(thick) + NL)
            f.write("Rejection Temperature, " + str(tavg) + NL)
            f.write("Density Of Water, -1" + NL)
            f.write("Heat Capacity Of Water, -1" + NL)


#with that file, run the HIP Python program to get a single HIP value
        sys.argv = ['', "D:\\Work\\ProjectCanary\\"+id+".txt", "D:\\Work\\ProjectCanary\\"+id+"_result.txt"]
        runpy.run_path("D:\\Work\\GEOPHIRES3-master\\HIP-RA.py", run_name='__main__')

#Now we have an single HIP result, so we need to update the ArcGIS table
        with open("D:\\Work\\ProjectCanary\\"+id+"_result.txt", "r") as f: text = f.readlines()
        for line in text:
            if "Produceable Electricity:" in line:
                s = line.split(":")
                s[1] = s[1].replace(' MW', '')
                PA =  float(s[1].strip())

        expression = u'{} = '.format(arcpy.AddFieldDelimiters(FootPrints, "gppd_idnr")) + "'" + str(id) + "'"
        with arcpy.da.UpdateCursor(FootPrints, ["HIP_PA"], expression) as cursor:
            for row in cursor:
                row[0] = PA
                cursor.updateRow(row)

#copy the contents of the master MC_Setting file into a new settings file
        shutil.copyfile("D:\\Work\\ProjectCanary\\MC_HIP_Settings_file.txt","D:\\Work\\ProjectCanary\\"+id+"_MCSettings.txt")

# add a line to the MC setting file to override the outfile name
        with open("D:\\Work\\ProjectCanary\\"+id+"_MCSettings.txt", "a") as f: f.write("MC_OUTPUT_FILE, D:\\Work\\ProjectCanary\\"+id+"_MCResults.txt")
# add a line to the MC setting file to set up a MC substitution range on the possible ambient temperatures
        with open("D:\\Work\\ProjectCanary\\"+id+"_MCSettings.txt", "a") as f: f.write(NL+"INPUT, Rejection Temperature, triangular, " + str(tmin) + ", " + str(tavg) + ", " + str(tmax))
# add a line to the MC setting file to set up a MC substitution range on the possible reservoir areas
        with open("D:\\Work\\ProjectCanary\\"+id+"_MCSettings.txt", "a") as f: f.write(NL+"INPUT, Reservoir Area, uniform, " + str(0.9*area) + ", " + str(area*1.1))
# add a line to the MC setting file to set up a MC substitution range on the possible reservoir thicknesses
        with open("D:\\Work\\ProjectCanary\\"+id+"_MCSettings.txt", "a") as f: f.write(NL+"INPUT, Reservoir Thickness, uniform, " + str(0.9*thick) + ", " + str(thick*1.1))

#Now run the MC Simulation
        sys.argv = ['', "D:\\Work\\GEOPHIRES3-master\\HIP_RA.py", "D:\\Work\\ProjectCanary\\"+id+".txt", "D:\\Work\\ProjectCanary\\"+id+"_MCSettings.txt"]
        runpy.run_path("D:\\Work\\GEOPHIRES3-master\\MC_GeoPHIRES3.py", run_name='__main__')
        os.remove("D:\\Work\\ProjectCanary\\"+id+"_MCSettings.txt")

#Now we have an MC result, so we need to update the ArcGIS table
        with open("D:\\Work\\ProjectCanary\\"+id+"_MCResults.txt", "r") as f: text = f.readlines()
        for line in text:
            if ":" in line:
                s = line.split(":")
                if "minimum" in s[0]: MCMin = float(s[1].strip())
                if "maximum" in s[0]: MCMax = float(s[1].strip())
                if "median" in s[0]: MCMedian = float(s[1].strip())
                if "average" in s[0]: MCAvg = float(s[1].strip())
                if "mean" in s[0]: MCMean = float(s[1].strip())
                if "standard deviation" in s[0]: MCStDev = float(s[1].strip())
                if "variance" in s[0]: MCVar = float(s[1].strip())

        with arcpy.da.UpdateCursor(FootPrints, ["HIP_PA_MC_Min","HIP_PA_MC_Max","HIP_PA_MC_Median","HIP_PA_MC_Average","HIP_PA_MC_Mean","HIP_PA_MC_Std_Dev","HIP_PA_MC_Variance"], expression) as cursor:
            for row in cursor:
                row[0] = MCMin
                row[1] = MCMax
                row[2] = MCMedian
                row[3] = MCAvg
                row[4] = MCMean
                row[5] = MCStDev
                row[6] = MCVar
                cursor.updateRow(row)
