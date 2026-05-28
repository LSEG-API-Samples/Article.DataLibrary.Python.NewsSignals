# Turning Headlines into Signals: Using Structured News Metadata to Understand Energy Market Disruptions

## <a id="overview"></a>Overview
Every day, LSEG delivers thousands of Reuters News stories touching the energy sector — pipeline outages, refinery fires, OPEC production adjustments, conflict, sanctions, weather events, regulatory changes. For an analyst trying to build a systematic view of energy supply disruptions, the challenge is not volume; it is **relevance**.

This notebook demonstrates how to use the **structured classification metadata** (QCodes) that Reuters News attaches to every story to define a precise, repeatable signal for energy supply disruptions — replacing noisy keyword searches with filters that match **meaning, not language**.

The workflow covers:
1. **Comparing** keyword search vs. structured metadata queries and quantifying the noise difference
2. **Defining** a supply disruption signal using sector, topic, and geographic classification codes
3. **Retrieving and validating** stories that match the structured signal
4. **Measuring** headline frequency over time to identify disruption spikes
5. **Decomposing** peak days using metadata to understand what drove the spike

The project also includes a helper package — `newsmetadata` — which provides a simple interface for resolving classification codes into descriptive labels, navigating parent-child relationships, and extracting metadata from individual stories.

Details and concepts are further explained in the [Turning Headlines into Signals](https://developers.lseg.com/en/article-catalog/article/turning-headlines-into-signals) article published on the [LSEG Developer Community portal](https://developers.lseg.com).

## <a id="disclaimer"></a>Disclaimer
The source code presented in this project has been written by LSEG only for the purpose of illustrating the concepts of creating example scenarios using the LSEG Data Library for Python.

***Note:** To [ask questions](https://community.developers.lseg.com/index.html) and benefit from the learning material, I recommend you to register on the [LSEG Developer Community](https://developers.lseg.com)*

## <a name="prerequisites"></a>Prerequisites

To execute the workbook, refer to the following:

License(s):

- An LSEG Workspace desktop license that has API access 


Development Environment

- Tested with Python 3.12.14
- Packages: [lseg-data](https://pypi.org/project/lseg-data/) [pandas](https://pypi.org/project/pandas/) [plotly](https://pypi.org/project/plotly/)
- LSEG Data Library for Python installation:  '**pip install lseg-data**'

## <a name="setup"></a>Setup

The package includes a single Jupyter Notebook demonstrating features of the service.  Depending where you plan to access the content from, you will need provide the proper credentials:
* **Desktop Access**
  
  The notebook has been set up and tested to access data within the LSEG Workspace desktop application.

### <a id="authors"></a>Authors

* **Nick Zincone** - Release 1.0.  *Initial version*



