# Niffler: A DICOM Framework for Machine Learning Pipelines against Real-Time Radiology Images

Niffler is a real-time PACS receiver and metadata extractor framework. It consists of a metadata extractor at its core. MetadataExtractor.py in src/meta-extraction implements the core extraction functionality.


## Using Niffler

Make sure to configure the PACS to send data to Niffler's host, port, and AE_Title. Niffler won't receive data unless the PACS allows the requests from Niffler (host/port/AE_Title).

In the src folder:

* cold-extraction: On-demand queries to retrieve retrospective DICOM data.

* meta-extraction: Extracts metadata from a continuous real-time DICOM imaging stream.

* png-extraction: Converts a set of DICOM images into png images, extract metadata in a privacy-preserving manner.


## Developing Niffler

Niffler core is built with Python3. The scanner utilization tool in the Application layer is built in Java and the individual scripts are developed in Javascript.

To develop the Niffler core, first, install the dependencies.

$ pip install requests pymongo schedule pydicom pynetdicom

For the development branch of pynetdicom

$ pip install git+git://github.com/pydicom/pynetdicom.git

Also install DCM4CHE from https://github.com/dcm4che/dcm4che/releases


The Java components of Niffler Application Layer are managed via Apache Maven 3.

Please refer to each module's individual README for additional instructions.


## Citing Niffler
If you use Niffler in your research, please cite the below paper:

* Kathiravelu, Pradeeban, Ashish Sharma, Saptarshi Purkayastha, Priyanshu Sinha, Alexandre Cadrin-Chenevert, Imon Banerjee, and Judy Wawira Gichoya. **Developing and Deploying Machine Learning Pipelines against Real-Time Image Streams from the PACS.** arXiv preprint arXiv:2004.07965 (2020).


