import math
import numpy as np
import sys
import os
#########################calculation parameters#########################
PI = 3.1415926
esp2 = 10.0e-10
#########################Results file creation##########################
fp_temperature = open("temperature.txt", "w")
if fp_temperature is None:
    print("error on freopen")
    exit(1)
#########################Thermal properties#############################
density_fluid = 1000.0#########waer density, kg/m3
Cp_fluid = 4180.0##############water specific heat capacity, J/kg/C
density_rock = 2663.0###########Rock/Reservoir bulk density, kg/m3
Cp_rock = 1112.0########Rock/reservoir bulk specific heat capacity, J/kg/C
kT_fluid = 0.6############Water thermal conductivity, W/m/K
kT_rock = 4.0############Rock/Reservoir bulk thermal conductivity, W/m/K

alpha_fluid = kT_fluid / density_fluid / Cp_fluid * 24.0 * 3600.0
alpha_rock = kT_rock / density_rock / Cp_rock * 24.0 * 3600.0
##################reservoir and wellbore geometry setup#################
x_boundary = 1.0e5
y_boundary = 1.0e5
z_boundary = 1.0e5
# no diff bewtween 0.85e2 or 2.0e15 
#all vals were 1.0e5 
y_well = 0.5 * y_boundary###Horizontal wellbore in the center
z_well = 0.5 * z_boundary###Horizontal wellbore in the center
###########################System design parameters#####################
Tini = 375.0 #MIR 120.0######Target geothermal reservoir initial temperature, C
l_pipe = 4000 #MIR 5000.0##########Horizontal wellbore length, m
diameter = 0.2    #MIR 0.156##############Horizontal wellbore diameter, m
area = PI * (diameter * 0.5) * (diameter * 0.5)
q_circulation = 6   #MIR 18.0/3.0##############Water circulation rate, m3/hour
velocity = q_circulation / area * 24.0
Tinlet = 60.0#################Inlet water temperature, C
###########################Time, computing control######################
al = 365.0######Time step, days
time_operation = 0.01 * 365.0#########First calculation date, days
time_max = 365.0 * 30.0###############Last calculation date, days
################################Numerical Laplace transformation algorism#########################
def inverselaplace(NL, MM):
    V = np.zeros(50)
    Gi = np.zeros(50)
    H = np.zeros(25)
    DLN2 = 0.6931471805599453
    FI = 0.0
    SN = 0.0
    Az = 0.0
    Z = 0.0
    
    if NL != MM:
        Gi[1] = 1.0
        NH = NL // 2
        SN = 2.0 * (NH % 2) - 1.0
        
        for i in range(1,NL+1):
            Gi[i + 1] = Gi[i] * (i)
            
        H[1] = 2.0 / Gi[NH]
        for i in range(1,NH+1):
            FI = i
            H[i] = math.pow(FI, NH) * Gi[2 * i + 1] / Gi[NH - i+1] / Gi[i + 1] / Gi[i]
            
        for i in range(1,NL+1):
            V[i] = 0.0
            KBG = (i + 1) // 2
            temp = NH if i >= NH else i
            KND = temp
            for k in range(KBG, KND+1):
                V[i] = V[i] + H[k] / Gi[i - k + 1] / Gi[2 * k - i + 1]
            V[i] = SN * V[i]
            SN = -SN
        MM = NL
    
    FI = 0.0
    Az = DLN2 / time_operation
    Toutlet = 0.0
    for k in range(1,NL+1):
        Z = Az * (k)
        Toutletl = laplace_solution(Z)
        Toutlet += Toutletl * V[k]
    Toutlet = Tini-Az * Toutlet
    return Toutlet
##################################################Duhamerl convolution method for closed-loop system######################################
def laplace_solution(sp):
    Toutletl = 0.0
    ss = 1.0 / sp / chebeve_pointsource(y_well, z_well, y_well, z_well-0.078, y_boundary, z_boundary, alpha_rock, sp)
  
    Toutletl = (Tini - Tinlet) / sp * np.exp(-sp * ss / q_circulation / 24.0 / density_fluid / Cp_fluid * l_pipe - sp / velocity * l_pipe)
    return Toutletl
############################################point source/sink solution functions#########################################
def thetaY(yt, ye, alpha, t):
    y = 0
    y1 = 0
    i = 0
    while abs(1.0 / math.sqrt(PI*alpha*t) * math.exp(-(yt + 2 * i*ye) * (yt + 2 * i*ye) / 4.0 / alpha / t)) > esp2:
        i += 1
    k = -1
    while abs(1.0 / math.sqrt(PI*alpha*t) * math.exp(-(yt + 2 * k*ye) * (yt + 2 * k*ye) / 4.0 / alpha / t)) > esp2:
        k -= 1
    for j in range(i, -1, -1):
        y += 1.0 / math.sqrt(PI*alpha*t) * math.exp(-(yt + 2 * j*ye) * (yt + 2 * j*ye) / 4.0 / alpha / t)
    for w in range(k, 0):
        y1 += 1.0 / math.sqrt(PI*alpha*t) * math.exp(-(yt + 2 * w*ye) * (yt + 2 * w*ye) / 4.0 / alpha / t)
    return y + y1

def thetaZ(zt, ze, alpha, t):
    y = 0
    y1 = 0
    i = 0
    while abs(1.0 / math.sqrt(PI*alpha*t) * math.exp(-(zt + 2 * i*ze) * (zt + 2 * i*ze) / 4.0 / alpha / t)) > esp2:
        i += 1
    k = -1
    while abs(1.0 / math.sqrt(PI*alpha*t) * math.exp(-(zt + 2 * k*ze) * (zt + 2 * k*ze) / 4.0 / alpha / t)) > esp2:
        k -= 1
    for j in range(i, -1, -1):
        y += 1.0 / math.sqrt(PI*alpha*t) * math.exp(-(zt + 2 * j*ze) * (zt + 2 * j*ze) / 4.0 / alpha / t)
    for w in range(k, 0):
        y1 += 1.0 / math.sqrt(PI*alpha*t) * math.exp(-(zt + 2 * w*ze) * (zt + 2 * w*ze) / 4.0 / alpha / t)
    return y + y1

def pointsource(yy, zz, yt, zt, ye, ze, alpha, sp, t):
    z = 1.0 / density_rock / Cp_rock / 4.0 * (thetaY(yt - yy, ye, alpha, t) + thetaY(yt + yy, ye, alpha, t)) * (thetaZ(zt - zz, ze, alpha, t) + thetaZ(zt + zz, ze, alpha, t)) * math.exp(-sp*t)
    return z
############################################Chebyshev approximation for numerical Laplace transformation integration from 1e-8 to 1e30##############################
def Chebyshev(a, b, n,yy, zz, yt, zt, ye, ze, alpha, sp, func):
    bma = 0.5 * (b - a)
    bpa = 0.5 * (b + a)
    f = [func(yy, zz, yt, zt, ye, ze, alpha, sp,math.cos(math.pi * (k + 0.5) / n) * bma + bpa) for k in range(n)]
    fac = 2.0 / n
    c = [fac * np.sum([f[k] * math.cos(PI * j * (k + 0.5) / n)
                  for k in range(n)]) for j in range(n)]
    con=0.25*(b-a)
    fac2=1.0
    cint=np.zeros(513)
    sum=0.0
    for j in range (1,n-1):
        cint[j]=con*(c[j-1]-c[j+1])/j
        sum += fac2*cint[j]
        fac2=-fac2
        cint[n-1]=con*c[n-2]/(n-1)
        sum += fac2*cint[n-1]
        cint[0]=2.0*sum   
    d=0.0
    dd=0.0
    y = (2.0 * b - a - b) * (1.0 / (b - a))
    y2 = 2.0 * y   
    for j in range (n-1,0,-1):
        sv=d
        d=y2*d-dd+cint[j]
        dd=sv   
    return y * d - dd + 0.5 *cint[0]   # Last step is different

def chebeve_pointsource(yy, zz, yt, zt, ye, ze, alpha, sp):
    m=32
    t_1 = 1.0e-8
    n = int(math.log10(1.0e4 / 1.0e-8) + 1)
    #t_2 = t_1 * 10 ** n
    a = t_1
    temp = 0.0
    for i in range(1, n + 1):
        b = a * 10.0
        temp = temp + Chebyshev(a,b,m,yy, zz, yt, zt, ye, ze, alpha, sp,pointsource)
        a = b
    ret = temp + (1 / sp * (math.exp(-sp * 1.0e5) - math.exp(-sp * 1.0e30))) / (ye * ze) / density_rock / Cp_rock
    return ret
##################################################Write results to .text file#######################################################
with open("temperature.txt", "w") as fp_temperature:
    while time_operation <= time_max:
        Toutlet=inverselaplace(16, 0)

        print("Toutlet=%f\t\n" % Toutlet)
        fp_temperature.write("%f\n" % Toutlet)

        time_operation += al

fp_temperature.close()