# Installation files

This folder contains the files needed to create the **conda environments** required to run different parts of **Lab 3**.

Each `.yml` file defines an **individual environment**, focused on a specific part of the project.  
You can install **one or both**, and then activate the environment that corresponds to what you want to run.

In general, you will find something like:

- An environment dedicated to **radiomic feature extraction** (PyRadiomics, SimpleITK, etc.).
- Another environment for the **rest of the code**: preprocessing of CSVs, statistical analysis and machine learning using already computed radiomic features.
