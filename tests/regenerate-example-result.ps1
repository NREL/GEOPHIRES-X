# Get the directory of the script
$scriptDir = Split-Path -Path $MyInvocation.MyCommand.Definition -Parent
# Change to the script directory
Set-Location -Path $scriptDir
# Run Python module
python -m geophires_x examples\$($args[0]).txt examples\$($args[0]).out
# Remove JSON file
Remove-Item -Path "examples\$($args[0]).json"
cd ..


#for example, this will reset the *.out files for some but not all the output files:
#./tests/regenerate-example-result.ps1 example1
#./tests/regenerate-example-result.ps1 example10_HP
#./tests/regenerate-example-result.ps1 example11_AC
#./tests/regenerate-example-result.ps1 example12_DH
#./tests/regenerate-example-result.ps1 example13
#./tests/regenerate-example-result.ps1 example1_addons
#./tests/regenerate-example-result.ps1 example2
#./tests/regenerate-example-result.ps1 example3
#./tests/regenerate-example-result.ps1 example4
#./tests/regenerate-example-result.ps1 example5
#./tests/regenerate-example-result.ps1 example8
#./tests/regenerate-example-result.ps1 example9
#./tests/regenerate-example-result.ps1 example_ITC
#./tests/regenerate-example-result.ps1 example_multiple_gradients
#./tests/regenerate-example-result.ps1 example_overpressure
#./tests/regenerate-example-result.ps1 example_overpressure2
#./tests/regenerate-example-result.ps1 example_PTC
#./tests/regenerate-example-result.ps1 example_SHR-1
#./tests/regenerate-example-result.ps1 example_SHR-2
#./tests/regenerate-example-result.ps1 Fervo_Norbeck_Latimer_2024
#./tests/regenerate-example-result.ps1 Wanju_Yuan_Closed-Loop_Geothermal_Energy_Recovery
