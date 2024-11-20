
Changelog
=========

GEOPHIRES-X (2023-2024)
------------------------

3.6
^^^

`release <https://github.com/NREL/GEOPHIRES-X/releases/tag/v3.6.0>`__ | `diff <https://github.com/NREL/GEOPHIRES-X/compare/v3.5.0...v3.6.0>`__

Changes default output file path to the original working directory instead of the the GEOPHIRES module source directory (usually ``geophires-x`` or ``src/geophires_x``, depending on package installation type).
This affects:

1. Users who call GEOPHIRES as a script from a working directory outside of the module source directory and pass no output file argument or a non-absolute output file argument e.g. ``python ./geophires-x/GEOPHIRESv3.py my-input.txt``. In prior versions, the output file would have been generated at ``./geophires_x/HDR.out``; in v.3.6 it is generated at ``./HDR.out`` instead. (Users who call GEOPHIRES as a module – ``python -m geophires_x my-input.txt`` – will see no change since the module has always output relative to the working directory.)

2. Inputs with ``HTML Output File`` and/or ``Improved Text Output File`` parameters specified as non-absolute paths. The associated output files will now be generated relative to the working directory instead of the GEOPHIRES module source directory.


Affected users who do not want the new behavior can specify absolute output paths instead of relative ones e.g. ``python ./geophires-x/GEOPHIRESv3.py my-input.txt /home/user/my-geophires-project/geophires-x/HDR.out``
(Most users are expected to be unaffected.)

3.6.1: Fixed Internal Rate default value changed to 7% from 6.25% per https://github.com/NREL/GEOPHIRES-X/issues/301

3.6.3: Discount Rate and Fixed Internal Rate are now synonymous. If one is provided, the other's value will be automatically set to the same value.

3.5
^^^

`release <https://github.com/NREL/GEOPHIRES-X/releases/tag/v3.5.0>`__ | `diff <https://github.com/NREL/GEOPHIRES-X/compare/v3.4.0...v3.5.0>`__

Milestone version for case studies, SHR temperatures, and other changes since 3.0.
An overview is given in the July 2024 NREL GEOPHIRES Workshop `Version 3.5 Announcement session recording <https://youtu.be/Bi_l6y6_LQk>`__.

3.5.3: SBT Reservoir Model (Slender Body Theory)

3.4
^^^

`release <https://github.com/NREL/GEOPHIRES-X/releases/tag/v3.4.0>`__ | `diff <https://github.com/NREL/GEOPHIRES-X/compare/v3.3.0...v3.4.0>`__

Monte Carlo moved to dedicated module

3.3
^^^

`release <https://github.com/NREL/GEOPHIRES-X/releases/tag/v3.3.0>`__ | `diff <https://github.com/NREL/GEOPHIRES-X/compare/v3.2.0...v3.3.0>`__

- Surface plant objectification. Note: some input values of ``End-Use Option`` will need to be updated to ``Plant Type``, see `SUTRAExample1.txt update for example <https://github.com/softwareengineerprogrammer/GEOPHIRES-X/commit/c7ded3dbf01577d9f92fe39ee8cc921e0cf4b9e2#diff-2defdec554de21ee27fb205f3418b138d8c55fa74ea49281f536e9453df4c973R30-R32>`__
- Introduction of HIP-RA-X



3.2
^^^
`release <https://github.com/NREL/GEOPHIRES-X/releases/tag/v3.2.0>`__ | `diff <https://github.com/NREL/GEOPHIRES-X/compare/v3.1.0...v3.2.0>`__

Bug fixes

3.1
^^^
`release <https://github.com/NREL/GEOPHIRES-X/releases/tag/v3.1.0>`__ | `diff <https://github.com/NREL/GEOPHIRES-X/compare/v3.0.0...v3.1.0>`__

Internal changes to support unit testing


3.0
^^^
`release <https://github.com/NREL/GEOPHIRES-X/releases/tag/v3.0.0>`__

- New repository: https://github.com/NREL/GEOPHIRES-X (Originally https://github.com/NREL/python-geophires-x, renamed to GEOPHIRES-X 2023-12-15 per https://github.com/NREL/GEOPHIRES-X/issues/48.)
- Ported from `malcolm-dsider/GEOPHIRES-X <https://github.com/malcolm-dsider/GEOPHIRES-X>`__ and `softwareengineerprogrammer/python-geophires-x <https://github.com/softwareengineerprogrammer/python-geophires-x>`__ using `ionelmc/cookiecutter-pylibrary <https://github.com/ionelmc/cookiecutter-pylibrary/>`__.
- Releases now marked with tags/version metadata generated with ``bumpversion``

2.0 (2019)
----------

* `GEOPHIRES v2.0 </References/Beckers%202019%20GEOPHIRES%20v2.pdf>`__
* https://github.com/NREL/GEOPHIRES-v2
* https://www.nrel.gov/docs/fy18osti/70856.pdf


1.0 (2013)
------------

* `GEOPHIRES v1 </References/Beckers%202013%20GEOPHIRES%20v1.pdf>`__
