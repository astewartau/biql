---
title: BIQL Tutorial
nav_order: 3
---

# BIQL Tutorial

This tutorial demonstrates how to use the BIDS Query Language (BIQL) to query neuroimaging datasets.
The examples below are automatically executed and updated whenever the documentation is built.


Welcome to the BIQL (BIDS Query Language) tutorial! This guide will walk you through
using BIQL to query BIDS neuroimaging datasets. We'll start with basic queries and
progressively explore more advanced features.

## What is BIQL?

BIQL is a SQL-like query language designed specifically for querying Brain Imaging 
Data Structure (BIDS) datasets. It allows you to:

- Search for specific files based on BIDS entities (subject, session, task, etc.)
- Filter data using metadata from JSON sidecars
- Access participant information from participants.tsv
- Perform aggregations and grouping operations
- Export results in various formats

## Prerequisites

First, let's set up our environment and get the example data:


```python
import tempfile
from pathlib import Path
from biql import create_query_engine

# Set up paths - use a temporary directory that works in different environments
bids_examples_dir = Path(tempfile.gettempdir()) / "bids-examples"

# Clone bids-examples if it doesn't exist
if not bids_examples_dir.exists():
    !git clone https://github.com/bids-standard/bids-examples.git {bids_examples_dir}
else:
    print(f"✅ bids-examples already exists at {bids_examples_dir}")
```

    Cloning into '/tmp/bids-examples'...


    remote: Enumerating objects: 30595, done.[K
    remote: Counting objects:   0% (1/1900)[Kremote: Counting objects:   1% (19/1900)[Kremote: Counting objects:   2% (38/1900)[Kremote: Counting objects:   3% (57/1900)[Kremote: Counting objects:   4% (76/1900)[Kremote: Counting objects:   5% (95/1900)[Kremote: Counting objects:   6% (114/1900)[Kremote: Counting objects:   7% (133/1900)[Kremote: Counting objects:   8% (152/1900)[Kremote: Counting objects:   9% (171/1900)[Kremote: Counting objects:  10% (190/1900)[Kremote: Counting objects:  11% (209/1900)[Kremote: Counting objects:  12% (228/1900)[Kremote: Counting objects:  13% (247/1900)[Kremote: Counting objects:  14% (266/1900)[Kremote: Counting objects:  15% (285/1900)[Kremote: Counting objects:  16% (304/1900)[Kremote: Counting objects:  17% (323/1900)[Kremote: Counting objects:  18% (342/1900)[Kremote: Counting objects:  19% (361/1900)[Kremote: Counting objects:  20% (380/1900)[Kremote: Counting objects:  21% (399/1900)[Kremote: Counting objects:  22% (418/1900)[K

    remote: Counting objects:  23% (437/1900)[Kremote: Counting objects:  24% (456/1900)[Kremote: Counting objects:  25% (475/1900)[Kremote: Counting objects:  26% (494/1900)[Kremote: Counting objects:  27% (513/1900)[Kremote: Counting objects:  28% (532/1900)[Kremote: Counting objects:  29% (551/1900)[Kremote: Counting objects:  30% (570/1900)[Kremote: Counting objects:  31% (589/1900)[Kremote: Counting objects:  32% (608/1900)[Kremote: Counting objects:  33% (627/1900)[Kremote: Counting objects:  34% (646/1900)[Kremote: Counting objects:  35% (665/1900)[Kremote: Counting objects:  36% (684/1900)[Kremote: Counting objects:  37% (703/1900)[Kremote: Counting objects:  38% (722/1900)[Kremote: Counting objects:  39% (741/1900)[Kremote: Counting objects:  40% (760/1900)[Kremote: Counting objects:  41% (779/1900)[Kremote: Counting objects:  42% (798/1900)[Kremote: Counting objects:  43% (817/1900)[Kremote: Counting objects:  44% (836/1900)[Kremote: Counting objects:  45% (855/1900)[Kremote: Counting objects:  46% (874/1900)[Kremote: Counting objects:  47% (893/1900)[Kremote: Counting objects:  48% (912/1900)[Kremote: Counting objects:  49% (931/1900)[Kremote: Counting objects:  50% (950/1900)[Kremote: Counting objects:  51% (969/1900)[Kremote: Counting objects:  52% (988/1900)[Kremote: Counting objects:  53% (1007/1900)[Kremote: Counting objects:  54% (1026/1900)[Kremote: Counting objects:  55% (1045/1900)[Kremote: Counting objects:  56% (1064/1900)[Kremote: Counting objects:  57% (1083/1900)[Kremote: Counting objects:  58% (1102/1900)[Kremote: Counting objects:  59% (1121/1900)[Kremote: Counting objects:  60% (1140/1900)[Kremote: Counting objects:  61% (1159/1900)[Kremote: Counting objects:  62% (1178/1900)[Kremote: Counting objects:  63% (1197/1900)[Kremote: Counting objects:  64% (1216/1900)[Kremote: Counting objects:  65% (1235/1900)[Kremote: Counting objects:  66% (1254/1900)[Kremote: Counting objects:  67% (1273/1900)[Kremote: Counting objects:  68% (1292/1900)[Kremote: Counting objects:  69% (1311/1900)[Kremote: Counting objects:  70% (1330/1900)[Kremote: Counting objects:  71% (1349/1900)[Kremote: Counting objects:  72% (1368/1900)[Kremote: Counting objects:  73% (1387/1900)[Kremote: Counting objects:  74% (1406/1900)[Kremote: Counting objects:  75% (1425/1900)[Kremote: Counting objects:  76% (1444/1900)[Kremote: Counting objects:  77% (1463/1900)[Kremote: Counting objects:  78% (1482/1900)[Kremote: Counting objects:  79% (1501/1900)[Kremote: Counting objects:  80% (1520/1900)[Kremote: Counting objects:  81% (1539/1900)[Kremote: Counting objects:  82% (1558/1900)[Kremote: Counting objects:  83% (1577/1900)[Kremote: Counting objects:  84% (1596/1900)[Kremote: Counting objects:  85% (1615/1900)[Kremote: Counting objects:  86% (1634/1900)[Kremote: Counting objects:  87% (1653/1900)[Kremote: Counting objects:  88% (1672/1900)[Kremote: Counting objects:  89% (1691/1900)[Kremote: Counting objects:  90% (1710/1900)[Kremote: Counting objects:  91% (1729/1900)[Kremote: Counting objects:  92% (1748/1900)[Kremote: Counting objects:  93% (1767/1900)[Kremote: Counting objects:  94% (1786/1900)[Kremote: Counting objects:  95% (1805/1900)[Kremote: Counting objects:  96% (1824/1900)[Kremote: Counting objects:  97% (1843/1900)[Kremote: Counting objects:  98% (1862/1900)[Kremote: Counting objects:  99% (1881/1900)[Kremote: Counting objects: 100% (1900/1900)[Kremote: Counting objects: 100% (1900/1900), done.[K
    remote: Compressing objects:   0% (1/443)[Kremote: Compressing objects:   1% (5/443)[Kremote: Compressing objects:   2% (9/443)[Kremote: Compressing objects:   3% (14/443)[Kremote: Compressing objects:   4% (18/443)[Kremote: Compressing objects:   5% (23/443)[Kremote: Compressing objects:   6% (27/443)[Kremote: Compressing objects:   7% (32/443)[Kremote: Compressing objects:   8% (36/443)[Kremote: Compressing objects:   9% (40/443)[Kremote: Compressing objects:  10% (45/443)[Kremote: Compressing objects:  11% (49/443)[Kremote: Compressing objects:  12% (54/443)[Kremote: Compressing objects:  13% (58/443)[Kremote: Compressing objects:  14% (63/443)[Kremote: Compressing objects:  15% (67/443)[Kremote: Compressing objects:  16% (71/443)[Kremote: Compressing objects:  17% (76/443)[Kremote: Compressing objects:  18% (80/443)[Kremote: Compressing objects:  19% (85/443)[Kremote: Compressing objects:  20% (89/443)[K

    remote: Compressing objects:  21% (94/443)[K

    remote: Compressing objects:  22% (98/443)[K

    remote: Compressing objects:  23% (102/443)[K

    remote: Compressing objects:  24% (107/443)[Kremote: Compressing objects:  25% (111/443)[K

    remote: Compressing objects:  26% (116/443)[Kremote: Compressing objects:  27% (120/443)[Kremote: Compressing objects:  28% (125/443)[Kremote: Compressing objects:  29% (129/443)[Kremote: Compressing objects:  30% (133/443)[K

    remote: Compressing objects:  31% (138/443)[Kremote: Compressing objects:  32% (142/443)[Kremote: Compressing objects:  33% (147/443)[Kremote: Compressing objects:  34% (151/443)[Kremote: Compressing objects:  35% (156/443)[Kremote: Compressing objects:  36% (160/443)[Kremote: Compressing objects:  37% (164/443)[Kremote: Compressing objects:  38% (169/443)[Kremote: Compressing objects:  39% (173/443)[Kremote: Compressing objects:  40% (178/443)[Kremote: Compressing objects:  41% (182/443)[Kremote: Compressing objects:  42% (187/443)[Kremote: Compressing objects:  43% (191/443)[Kremote: Compressing objects:  44% (195/443)[Kremote: Compressing objects:  45% (200/443)[Kremote: Compressing objects:  46% (204/443)[Kremote: Compressing objects:  47% (209/443)[Kremote: Compressing objects:  48% (213/443)[Kremote: Compressing objects:  49% (218/443)[Kremote: Compressing objects:  50% (222/443)[Kremote: Compressing objects:  51% (226/443)[Kremote: Compressing objects:  52% (231/443)[Kremote: Compressing objects:  53% (235/443)[Kremote: Compressing objects:  54% (240/443)[Kremote: Compressing objects:  55% (244/443)[Kremote: Compressing objects:  56% (249/443)[Kremote: Compressing objects:  57% (253/443)[Kremote: Compressing objects:  58% (257/443)[Kremote: Compressing objects:  59% (262/443)[Kremote: Compressing objects:  60% (266/443)[Kremote: Compressing objects:  61% (271/443)[Kremote: Compressing objects:  62% (275/443)[Kremote: Compressing objects:  63% (280/443)[Kremote: Compressing objects:  64% (284/443)[Kremote: Compressing objects:  65% (288/443)[Kremote: Compressing objects:  66% (293/443)[Kremote: Compressing objects:  67% (297/443)[Kremote: Compressing objects:  68% (302/443)[Kremote: Compressing objects:  69% (306/443)[Kremote: Compressing objects:  70% (311/443)[Kremote: Compressing objects:  71% (315/443)[Kremote: Compressing objects:  72% (319/443)[Kremote: Compressing objects:  73% (324/443)[Kremote: Compressing objects:  74% (328/443)[Kremote: Compressing objects:  75% (333/443)[Kremote: Compressing objects:  76% (337/443)[Kremote: Compressing objects:  77% (342/443)[Kremote: Compressing objects:  78% (346/443)[Kremote: Compressing objects:  79% (350/443)[Kremote: Compressing objects:  80% (355/443)[Kremote: Compressing objects:  81% (359/443)[Kremote: Compressing objects:  82% (364/443)[Kremote: Compressing objects:  83% (368/443)[Kremote: Compressing objects:  84% (373/443)[Kremote: Compressing objects:  85% (377/443)[Kremote: Compressing objects:  86% (381/443)[Kremote: Compressing objects:  87% (386/443)[Kremote: Compressing objects:  88% (390/443)[Kremote: Compressing objects:  89% (395/443)[Kremote: Compressing objects:  90% (399/443)[Kremote: Compressing objects:  91% (404/443)[Kremote: Compressing objects:  92% (408/443)[Kremote: Compressing objects:  93% (412/443)[Kremote: Compressing objects:  94% (417/443)[Kremote: Compressing objects:  95% (421/443)[Kremote: Compressing objects:  96% (426/443)[Kremote: Compressing objects:  97% (430/443)[Kremote: Compressing objects:  98% (435/443)[Kremote: Compressing objects:  99% (439/443)[Kremote: Compressing objects: 100% (443/443)[Kremote: Compressing objects: 100% (443/443), done.[K
    Receiving objects:   0% (1/30595)

    Receiving objects:   1% (306/30595)Receiving objects:   2% (612/30595)Receiving objects:   3% (918/30595)Receiving objects:   4% (1224/30595)Receiving objects:   5% (1530/30595)

    Receiving objects:   6% (1836/30595)Receiving objects:   7% (2142/30595)Receiving objects:   8% (2448/30595)Receiving objects:   9% (2754/30595)Receiving objects:  10% (3060/30595)Receiving objects:  11% (3366/30595)Receiving objects:  12% (3672/30595)Receiving objects:  13% (3978/30595)Receiving objects:  14% (4284/30595)

    Receiving objects:  15% (4590/30595)Receiving objects:  16% (4896/30595)Receiving objects:  17% (5202/30595)Receiving objects:  18% (5508/30595)Receiving objects:  19% (5814/30595)Receiving objects:  20% (6119/30595)Receiving objects:  21% (6425/30595)Receiving objects:  22% (6731/30595)Receiving objects:  23% (7037/30595)Receiving objects:  24% (7343/30595)Receiving objects:  25% (7649/30595)Receiving objects:  26% (7955/30595)Receiving objects:  27% (8261/30595)

    Receiving objects:  28% (8567/30595)

    Receiving objects:  29% (8873/30595)

    Receiving objects:  30% (9179/30595)

    Receiving objects:  31% (9485/30595)

    Receiving objects:  32% (9791/30595)

    Receiving objects:  33% (10097/30595), 23.53 MiB | 47.04 MiB/sReceiving objects:  34% (10403/30595), 23.53 MiB | 47.04 MiB/sReceiving objects:  35% (10709/30595), 23.53 MiB | 47.04 MiB/s

    Receiving objects:  36% (11015/30595), 23.53 MiB | 47.04 MiB/sReceiving objects:  37% (11321/30595), 23.53 MiB | 47.04 MiB/s

    Receiving objects:  38% (11627/30595), 23.53 MiB | 47.04 MiB/s

    Receiving objects:  39% (11933/30595), 23.53 MiB | 47.04 MiB/sReceiving objects:  40% (12238/30595), 23.53 MiB | 47.04 MiB/s

    Receiving objects:  41% (12544/30595), 23.53 MiB | 47.04 MiB/sReceiving objects:  42% (12850/30595), 23.53 MiB | 47.04 MiB/sReceiving objects:  43% (13156/30595), 23.53 MiB | 47.04 MiB/sReceiving objects:  44% (13462/30595), 23.53 MiB | 47.04 MiB/sReceiving objects:  45% (13768/30595), 23.53 MiB | 47.04 MiB/sReceiving objects:  46% (14074/30595), 23.53 MiB | 47.04 MiB/sReceiving objects:  47% (14380/30595), 23.53 MiB | 47.04 MiB/s

    Receiving objects:  48% (14686/30595), 23.53 MiB | 47.04 MiB/sReceiving objects:  49% (14992/30595), 23.53 MiB | 47.04 MiB/sReceiving objects:  50% (15298/30595), 23.53 MiB | 47.04 MiB/sReceiving objects:  51% (15604/30595), 23.53 MiB | 47.04 MiB/sReceiving objects:  52% (15910/30595), 23.53 MiB | 47.04 MiB/sReceiving objects:  53% (16216/30595), 23.53 MiB | 47.04 MiB/sReceiving objects:  54% (16522/30595), 23.53 MiB | 47.04 MiB/sReceiving objects:  55% (16828/30595), 23.53 MiB | 47.04 MiB/sReceiving objects:  56% (17134/30595), 23.53 MiB | 47.04 MiB/sReceiving objects:  57% (17440/30595), 23.53 MiB | 47.04 MiB/sReceiving objects:  58% (17746/30595), 23.53 MiB | 47.04 MiB/sReceiving objects:  59% (18052/30595), 23.53 MiB | 47.04 MiB/s

    Receiving objects:  60% (18357/30595), 23.53 MiB | 47.04 MiB/sReceiving objects:  61% (18663/30595), 23.53 MiB | 47.04 MiB/sReceiving objects:  62% (18969/30595), 23.53 MiB | 47.04 MiB/sReceiving objects:  63% (19275/30595), 23.53 MiB | 47.04 MiB/sReceiving objects:  64% (19581/30595), 23.53 MiB | 47.04 MiB/s

    Receiving objects:  64% (19791/30595), 42.89 MiB | 42.88 MiB/s

    Receiving objects:  65% (19887/30595), 42.89 MiB | 42.88 MiB/sReceiving objects:  66% (20193/30595), 42.89 MiB | 42.88 MiB/sReceiving objects:  67% (20499/30595), 42.89 MiB | 42.88 MiB/sReceiving objects:  68% (20805/30595), 42.89 MiB | 42.88 MiB/sReceiving objects:  69% (21111/30595), 42.89 MiB | 42.88 MiB/s

    Receiving objects:  70% (21417/30595), 42.89 MiB | 42.88 MiB/sReceiving objects:  71% (21723/30595), 42.89 MiB | 42.88 MiB/sReceiving objects:  72% (22029/30595), 42.89 MiB | 42.88 MiB/sReceiving objects:  73% (22335/30595), 42.89 MiB | 42.88 MiB/sReceiving objects:  74% (22641/30595), 42.89 MiB | 42.88 MiB/sReceiving objects:  75% (22947/30595), 42.89 MiB | 42.88 MiB/s

    Receiving objects:  76% (23253/30595), 81.04 MiB | 54.02 MiB/sReceiving objects:  77% (23559/30595), 81.04 MiB | 54.02 MiB/s

    Receiving objects:  78% (23865/30595), 81.04 MiB | 54.02 MiB/sReceiving objects:  79% (24171/30595), 81.04 MiB | 54.02 MiB/sReceiving objects:  80% (24476/30595), 81.04 MiB | 54.02 MiB/sReceiving objects:  81% (24782/30595), 81.04 MiB | 54.02 MiB/sReceiving objects:  82% (25088/30595), 81.04 MiB | 54.02 MiB/s

    Receiving objects:  83% (25394/30595), 81.04 MiB | 54.02 MiB/sReceiving objects:  84% (25700/30595), 81.04 MiB | 54.02 MiB/sReceiving objects:  85% (26006/30595), 81.04 MiB | 54.02 MiB/sReceiving objects:  86% (26312/30595), 81.04 MiB | 54.02 MiB/sReceiving objects:  87% (26618/30595), 81.04 MiB | 54.02 MiB/sReceiving objects:  88% (26924/30595), 81.04 MiB | 54.02 MiB/sReceiving objects:  89% (27230/30595), 81.04 MiB | 54.02 MiB/sReceiving objects:  90% (27536/30595), 81.04 MiB | 54.02 MiB/sReceiving objects:  91% (27842/30595), 81.04 MiB | 54.02 MiB/sReceiving objects:  92% (28148/30595), 81.04 MiB | 54.02 MiB/s

    Receiving objects:  93% (28454/30595), 81.04 MiB | 54.02 MiB/s

    Receiving objects:  94% (28760/30595), 81.04 MiB | 54.02 MiB/sReceiving objects:  95% (29066/30595), 81.04 MiB | 54.02 MiB/sReceiving objects:  96% (29372/30595), 81.04 MiB | 54.02 MiB/sReceiving objects:  97% (29678/30595), 81.04 MiB | 54.02 MiB/sReceiving objects:  98% (29984/30595), 81.04 MiB | 54.02 MiB/sReceiving objects:  99% (30290/30595), 81.04 MiB | 54.02 MiB/sremote: Total 30595 (delta 1599), reused 1476 (delta 1453), pack-reused 28695 (from 2)[K
    Receiving objects: 100% (30595/30595), 81.04 MiB | 54.02 MiB/sReceiving objects: 100% (30595/30595), 100.06 MiB | 54.85 MiB/s, done.
    Resolving deltas:   0% (0/15576)

    Resolving deltas:   1% (156/15576)Resolving deltas:   2% (312/15576)Resolving deltas:   3% (468/15576)Resolving deltas:   4% (624/15576)Resolving deltas:   5% (779/15576)Resolving deltas:   6% (935/15576)Resolving deltas:   7% (1091/15576)Resolving deltas:   8% (1247/15576)Resolving deltas:   9% (1403/15576)Resolving deltas:  10% (1558/15576)Resolving deltas:  11% (1714/15576)Resolving deltas:  12% (1870/15576)Resolving deltas:  13% (2025/15576)Resolving deltas:  14% (2181/15576)Resolving deltas:  15% (2337/15576)Resolving deltas:  16% (2493/15576)Resolving deltas:  17% (2648/15576)Resolving deltas:  18% (2804/15576)Resolving deltas:  19% (2960/15576)

    Resolving deltas:  20% (3116/15576)Resolving deltas:  21% (3271/15576)Resolving deltas:  22% (3427/15576)Resolving deltas:  23% (3583/15576)Resolving deltas:  24% (3739/15576)Resolving deltas:  25% (3894/15576)Resolving deltas:  26% (4050/15576)Resolving deltas:  27% (4206/15576)Resolving deltas:  28% (4362/15576)Resolving deltas:  29% (4518/15576)Resolving deltas:  30% (4673/15576)Resolving deltas:  31% (4829/15576)Resolving deltas:  32% (4985/15576)Resolving deltas:  33% (5141/15576)Resolving deltas:  34% (5296/15576)Resolving deltas:  35% (5453/15576)Resolving deltas:  36% (5608/15576)Resolving deltas:  37% (5764/15576)Resolving deltas:  38% (5919/15576)Resolving deltas:  39% (6075/15576)

    Resolving deltas:  40% (6231/15576)Resolving deltas:  41% (6387/15576)Resolving deltas:  42% (6542/15576)Resolving deltas:  43% (6698/15576)Resolving deltas:  44% (6854/15576)Resolving deltas:  45% (7011/15576)Resolving deltas:  46% (7166/15576)Resolving deltas:  47% (7321/15576)Resolving deltas:  48% (7477/15576)Resolving deltas:  49% (7633/15576)Resolving deltas:  50% (7788/15576)Resolving deltas:  51% (7944/15576)Resolving deltas:  52% (8100/15576)Resolving deltas:  53% (8256/15576)Resolving deltas:  54% (8412/15576)Resolving deltas:  55% (8567/15576)

    Resolving deltas:  56% (8723/15576)Resolving deltas:  57% (8879/15576)Resolving deltas:  58% (9035/15576)Resolving deltas:  59% (9190/15576)Resolving deltas:  60% (9346/15576)Resolving deltas:  61% (9502/15576)Resolving deltas:  62% (9658/15576)Resolving deltas:  63% (9813/15576)Resolving deltas:  64% (9969/15576)Resolving deltas:  65% (10126/15576)Resolving deltas:  66% (10281/15576)Resolving deltas:  67% (10438/15576)Resolving deltas:  68% (10592/15576)Resolving deltas:  69% (10748/15576)Resolving deltas:  70% (10904/15576)Resolving deltas:  71% (11059/15576)Resolving deltas:  72% (11216/15576)Resolving deltas:  73% (11371/15576)Resolving deltas:  74% (11527/15576)Resolving deltas:  75% (11682/15576)Resolving deltas:  76% (11838/15576)

    Resolving deltas:  77% (11994/15576)Resolving deltas:  78% (12150/15576)Resolving deltas:  79% (12306/15576)Resolving deltas:  80% (12461/15576)

    Resolving deltas:  81% (12617/15576)Resolving deltas:  82% (12773/15576)Resolving deltas:  83% (12929/15576)Resolving deltas:  84% (13084/15576)

    Resolving deltas:  85% (13240/15576)Resolving deltas:  86% (13396/15576)

    Resolving deltas:  87% (13552/15576)Resolving deltas:  88% (13707/15576)Resolving deltas:  89% (13863/15576)Resolving deltas:  90% (14019/15576)Resolving deltas:  91% (14175/15576)Resolving deltas:  92% (14330/15576)Resolving deltas:  93% (14486/15576)Resolving deltas:  94% (14642/15576)Resolving deltas:  95% (14798/15576)Resolving deltas:  96% (14953/15576)Resolving deltas:  97% (15109/15576)Resolving deltas:  98% (15265/15576)Resolving deltas:  99% (15421/15576)

    Resolving deltas: 100% (15576/15576)Resolving deltas: 100% (15576/15576), done.


## Part 1: Basic Queries

Let's start with the synthetic dataset from bids-examples. This is a simple dataset
that's perfect for learning BIQL basics.


```python
dataset_path = bids_examples_dir / "synthetic"
q = create_query_engine(dataset_path)

q.dataset_stats()
```




    {'total_files': 60,
     'total_subjects': 5,
     'files_by_datatype': {'anat': 10, 'func': 30, 'beh': 5},
     'subjects': ['01', '02', '03', '04', '05'],
     'datatypes': ['anat', 'beh', 'func']}



### Simple Entity Queries

The most basic BIQL queries filter files by BIDS entities. You can query by any
BIDS entity that appears in your filenames:


```python
q.run_query("sub=01", format="dataframe").head(5)
```




<div>
<style scoped>
    .dataframe tbody tr th:only-of-type {
        vertical-align: middle;
    }

    .dataframe tbody tr th {
        vertical-align: top;
    }

    .dataframe thead th {
        text-align: right;
    }
</style>
<table border="1" class="dataframe">
  <thead>
    <tr style="text-align: right;">
      <th></th>
      <th>filepath</th>
      <th>relative_path</th>
      <th>filename</th>
      <th>sub</th>
      <th>ses</th>
      <th>suffix</th>
      <th>datatype</th>
      <th>extension</th>
      <th>metadata</th>
      <th>participants</th>
      <th>task</th>
      <th>run</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <th>0</th>
      <td>/tmp/bids-examples/synthetic/sub-01/ses-02/ana...</td>
      <td>sub-01/ses-02/anat/sub-01_ses-02_T1w.nii</td>
      <td>sub-01_ses-02_T1w.nii</td>
      <td>01</td>
      <td>02</td>
      <td>T1w</td>
      <td>anat</td>
      <td>.nii</td>
      <td>{}</td>
      <td>age=34; sex=F</td>
      <td>NaN</td>
      <td>NaN</td>
    </tr>
    <tr>
      <th>1</th>
      <td>/tmp/bids-examples/synthetic/sub-01/ses-02/fun...</td>
      <td>sub-01/ses-02/func/sub-01_ses-02_task-nback_ru...</td>
      <td>sub-01_ses-02_task-nback_run-02_bold.nii</td>
      <td>01</td>
      <td>02</td>
      <td>bold</td>
      <td>func</td>
      <td>.nii</td>
      <td>{}</td>
      <td>age=34; sex=F</td>
      <td>nback</td>
      <td>02</td>
    </tr>
    <tr>
      <th>2</th>
      <td>/tmp/bids-examples/synthetic/sub-01/ses-02/fun...</td>
      <td>sub-01/ses-02/func/sub-01_ses-02_task-nback_ru...</td>
      <td>sub-01_ses-02_task-nback_run-01_bold.nii</td>
      <td>01</td>
      <td>02</td>
      <td>bold</td>
      <td>func</td>
      <td>.nii</td>
      <td>{}</td>
      <td>age=34; sex=F</td>
      <td>nback</td>
      <td>01</td>
    </tr>
    <tr>
      <th>3</th>
      <td>/tmp/bids-examples/synthetic/sub-01/ses-02/fun...</td>
      <td>sub-01/ses-02/func/sub-01_ses-02_task-rest_bol...</td>
      <td>sub-01_ses-02_task-rest_bold.nii</td>
      <td>01</td>
      <td>02</td>
      <td>bold</td>
      <td>func</td>
      <td>.nii</td>
      <td>{}</td>
      <td>age=34; sex=F</td>
      <td>rest</td>
      <td>NaN</td>
    </tr>
    <tr>
      <th>4</th>
      <td>/tmp/bids-examples/synthetic/sub-01/ses-01/ana...</td>
      <td>sub-01/ses-01/anat/sub-01_ses-01_T1w.nii</td>
      <td>sub-01_ses-01_T1w.nii</td>
      <td>01</td>
      <td>01</td>
      <td>T1w</td>
      <td>anat</td>
      <td>.nii</td>
      <td>{}</td>
      <td>age=34; sex=F</td>
      <td>NaN</td>
      <td>NaN</td>
    </tr>
  </tbody>
</table>
</div>




```python
results = q.run_query("datatype=func")
len(results)  # Number of functional files
```




    30




```python
q.run_query("SELECT DISTINCT task WHERE datatype=func", format="dataframe")
```




<div>
<style scoped>
    .dataframe tbody tr th:only-of-type {
        vertical-align: middle;
    }

    .dataframe tbody tr th {
        vertical-align: top;
    }

    .dataframe thead th {
        text-align: right;
    }
</style>
<table border="1" class="dataframe">
  <thead>
    <tr style="text-align: right;">
      <th></th>
      <th>task</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <th>0</th>
      <td>nback</td>
    </tr>
    <tr>
      <th>1</th>
      <td>rest</td>
    </tr>
  </tbody>
</table>
</div>



### Combining Conditions

You can combine multiple conditions using AND, OR, and NOT operators:


```python
q.run_query("datatype=anat AND suffix=T1w", format="dataframe").head(5)
```




<div>
<style scoped>
    .dataframe tbody tr th:only-of-type {
        vertical-align: middle;
    }

    .dataframe tbody tr th {
        vertical-align: top;
    }

    .dataframe thead th {
        text-align: right;
    }
</style>
<table border="1" class="dataframe">
  <thead>
    <tr style="text-align: right;">
      <th></th>
      <th>filepath</th>
      <th>relative_path</th>
      <th>filename</th>
      <th>sub</th>
      <th>ses</th>
      <th>suffix</th>
      <th>datatype</th>
      <th>extension</th>
      <th>metadata</th>
      <th>participants</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <th>0</th>
      <td>/tmp/bids-examples/synthetic/sub-01/ses-02/ana...</td>
      <td>sub-01/ses-02/anat/sub-01_ses-02_T1w.nii</td>
      <td>sub-01_ses-02_T1w.nii</td>
      <td>01</td>
      <td>02</td>
      <td>T1w</td>
      <td>anat</td>
      <td>.nii</td>
      <td>{}</td>
      <td>age=34; sex=F</td>
    </tr>
    <tr>
      <th>1</th>
      <td>/tmp/bids-examples/synthetic/sub-01/ses-01/ana...</td>
      <td>sub-01/ses-01/anat/sub-01_ses-01_T1w.nii</td>
      <td>sub-01_ses-01_T1w.nii</td>
      <td>01</td>
      <td>01</td>
      <td>T1w</td>
      <td>anat</td>
      <td>.nii</td>
      <td>{}</td>
      <td>age=34; sex=F</td>
    </tr>
    <tr>
      <th>2</th>
      <td>/tmp/bids-examples/synthetic/sub-04/ses-02/ana...</td>
      <td>sub-04/ses-02/anat/sub-04_ses-02_T1w.nii</td>
      <td>sub-04_ses-02_T1w.nii</td>
      <td>04</td>
      <td>02</td>
      <td>T1w</td>
      <td>anat</td>
      <td>.nii</td>
      <td>{}</td>
      <td>age=21; sex=F</td>
    </tr>
    <tr>
      <th>3</th>
      <td>/tmp/bids-examples/synthetic/sub-04/ses-01/ana...</td>
      <td>sub-04/ses-01/anat/sub-04_ses-01_T1w.nii</td>
      <td>sub-04_ses-01_T1w.nii</td>
      <td>04</td>
      <td>01</td>
      <td>T1w</td>
      <td>anat</td>
      <td>.nii</td>
      <td>{}</td>
      <td>age=21; sex=F</td>
    </tr>
    <tr>
      <th>4</th>
      <td>/tmp/bids-examples/synthetic/sub-05/ses-02/ana...</td>
      <td>sub-05/ses-02/anat/sub-05_ses-02_T1w.nii</td>
      <td>sub-05_ses-02_T1w.nii</td>
      <td>05</td>
      <td>02</td>
      <td>T1w</td>
      <td>anat</td>
      <td>.nii</td>
      <td>{}</td>
      <td>age=42; sex=M</td>
    </tr>
  </tbody>
</table>
</div>




```python
q.run_query("task=nback OR task=rest", format="dataframe")
```




<div>
<style scoped>
    .dataframe tbody tr th:only-of-type {
        vertical-align: middle;
    }

    .dataframe tbody tr th {
        vertical-align: top;
    }

    .dataframe thead th {
        text-align: right;
    }
</style>
<table border="1" class="dataframe">
  <thead>
    <tr style="text-align: right;">
      <th></th>
      <th>filepath</th>
      <th>relative_path</th>
      <th>filename</th>
      <th>sub</th>
      <th>ses</th>
      <th>task</th>
      <th>run</th>
      <th>suffix</th>
      <th>datatype</th>
      <th>extension</th>
      <th>metadata</th>
      <th>participants</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <th>0</th>
      <td>/tmp/bids-examples/synthetic/sub-01/ses-02/fun...</td>
      <td>sub-01/ses-02/func/sub-01_ses-02_task-nback_ru...</td>
      <td>sub-01_ses-02_task-nback_run-02_bold.nii</td>
      <td>01</td>
      <td>02</td>
      <td>nback</td>
      <td>02</td>
      <td>bold</td>
      <td>func</td>
      <td>.nii</td>
      <td>{}</td>
      <td>age=34; sex=F</td>
    </tr>
    <tr>
      <th>1</th>
      <td>/tmp/bids-examples/synthetic/sub-01/ses-02/fun...</td>
      <td>sub-01/ses-02/func/sub-01_ses-02_task-nback_ru...</td>
      <td>sub-01_ses-02_task-nback_run-01_bold.nii</td>
      <td>01</td>
      <td>02</td>
      <td>nback</td>
      <td>01</td>
      <td>bold</td>
      <td>func</td>
      <td>.nii</td>
      <td>{}</td>
      <td>age=34; sex=F</td>
    </tr>
    <tr>
      <th>2</th>
      <td>/tmp/bids-examples/synthetic/sub-01/ses-02/fun...</td>
      <td>sub-01/ses-02/func/sub-01_ses-02_task-rest_bol...</td>
      <td>sub-01_ses-02_task-rest_bold.nii</td>
      <td>01</td>
      <td>02</td>
      <td>rest</td>
      <td>NaN</td>
      <td>bold</td>
      <td>func</td>
      <td>.nii</td>
      <td>{}</td>
      <td>age=34; sex=F</td>
    </tr>
    <tr>
      <th>3</th>
      <td>/tmp/bids-examples/synthetic/sub-01/ses-01/fun...</td>
      <td>sub-01/ses-01/func/sub-01_ses-01_task-nback_ru...</td>
      <td>sub-01_ses-01_task-nback_run-02_bold.nii</td>
      <td>01</td>
      <td>01</td>
      <td>nback</td>
      <td>02</td>
      <td>bold</td>
      <td>func</td>
      <td>.nii</td>
      <td>{}</td>
      <td>age=34; sex=F</td>
    </tr>
    <tr>
      <th>4</th>
      <td>/tmp/bids-examples/synthetic/sub-01/ses-01/fun...</td>
      <td>sub-01/ses-01/func/sub-01_ses-01_task-rest_bol...</td>
      <td>sub-01_ses-01_task-rest_bold.nii</td>
      <td>01</td>
      <td>01</td>
      <td>rest</td>
      <td>NaN</td>
      <td>bold</td>
      <td>func</td>
      <td>.nii</td>
      <td>{}</td>
      <td>age=34; sex=F</td>
    </tr>
    <tr>
      <th>5</th>
      <td>/tmp/bids-examples/synthetic/sub-01/ses-01/fun...</td>
      <td>sub-01/ses-01/func/sub-01_ses-01_task-nback_ru...</td>
      <td>sub-01_ses-01_task-nback_run-01_bold.nii</td>
      <td>01</td>
      <td>01</td>
      <td>nback</td>
      <td>01</td>
      <td>bold</td>
      <td>func</td>
      <td>.nii</td>
      <td>{}</td>
      <td>age=34; sex=F</td>
    </tr>
    <tr>
      <th>6</th>
      <td>/tmp/bids-examples/synthetic/sub-04/ses-02/fun...</td>
      <td>sub-04/ses-02/func/sub-04_ses-02_task-nback_ru...</td>
      <td>sub-04_ses-02_task-nback_run-02_bold.nii</td>
      <td>04</td>
      <td>02</td>
      <td>nback</td>
      <td>02</td>
      <td>bold</td>
      <td>func</td>
      <td>.nii</td>
      <td>{}</td>
      <td>age=21; sex=F</td>
    </tr>
    <tr>
      <th>7</th>
      <td>/tmp/bids-examples/synthetic/sub-04/ses-02/fun...</td>
      <td>sub-04/ses-02/func/sub-04_ses-02_task-nback_ru...</td>
      <td>sub-04_ses-02_task-nback_run-01_bold.nii</td>
      <td>04</td>
      <td>02</td>
      <td>nback</td>
      <td>01</td>
      <td>bold</td>
      <td>func</td>
      <td>.nii</td>
      <td>{}</td>
      <td>age=21; sex=F</td>
    </tr>
    <tr>
      <th>8</th>
      <td>/tmp/bids-examples/synthetic/sub-04/ses-02/fun...</td>
      <td>sub-04/ses-02/func/sub-04_ses-02_task-rest_bol...</td>
      <td>sub-04_ses-02_task-rest_bold.nii</td>
      <td>04</td>
      <td>02</td>
      <td>rest</td>
      <td>NaN</td>
      <td>bold</td>
      <td>func</td>
      <td>.nii</td>
      <td>{}</td>
      <td>age=21; sex=F</td>
    </tr>
    <tr>
      <th>9</th>
      <td>/tmp/bids-examples/synthetic/sub-04/ses-01/fun...</td>
      <td>sub-04/ses-01/func/sub-04_ses-01_task-nback_ru...</td>
      <td>sub-04_ses-01_task-nback_run-02_bold.nii</td>
      <td>04</td>
      <td>01</td>
      <td>nback</td>
      <td>02</td>
      <td>bold</td>
      <td>func</td>
      <td>.nii</td>
      <td>{}</td>
      <td>age=21; sex=F</td>
    </tr>
    <tr>
      <th>10</th>
      <td>/tmp/bids-examples/synthetic/sub-04/ses-01/fun...</td>
      <td>sub-04/ses-01/func/sub-04_ses-01_task-rest_bol...</td>
      <td>sub-04_ses-01_task-rest_bold.nii</td>
      <td>04</td>
      <td>01</td>
      <td>rest</td>
      <td>NaN</td>
      <td>bold</td>
      <td>func</td>
      <td>.nii</td>
      <td>{}</td>
      <td>age=21; sex=F</td>
    </tr>
    <tr>
      <th>11</th>
      <td>/tmp/bids-examples/synthetic/sub-04/ses-01/fun...</td>
      <td>sub-04/ses-01/func/sub-04_ses-01_task-nback_ru...</td>
      <td>sub-04_ses-01_task-nback_run-01_bold.nii</td>
      <td>04</td>
      <td>01</td>
      <td>nback</td>
      <td>01</td>
      <td>bold</td>
      <td>func</td>
      <td>.nii</td>
      <td>{}</td>
      <td>age=21; sex=F</td>
    </tr>
    <tr>
      <th>12</th>
      <td>/tmp/bids-examples/synthetic/sub-05/ses-02/fun...</td>
      <td>sub-05/ses-02/func/sub-05_ses-02_task-rest_bol...</td>
      <td>sub-05_ses-02_task-rest_bold.nii</td>
      <td>05</td>
      <td>02</td>
      <td>rest</td>
      <td>NaN</td>
      <td>bold</td>
      <td>func</td>
      <td>.nii</td>
      <td>{}</td>
      <td>age=42; sex=M</td>
    </tr>
    <tr>
      <th>13</th>
      <td>/tmp/bids-examples/synthetic/sub-05/ses-02/fun...</td>
      <td>sub-05/ses-02/func/sub-05_ses-02_task-nback_ru...</td>
      <td>sub-05_ses-02_task-nback_run-02_bold.nii</td>
      <td>05</td>
      <td>02</td>
      <td>nback</td>
      <td>02</td>
      <td>bold</td>
      <td>func</td>
      <td>.nii</td>
      <td>{}</td>
      <td>age=42; sex=M</td>
    </tr>
    <tr>
      <th>14</th>
      <td>/tmp/bids-examples/synthetic/sub-05/ses-02/fun...</td>
      <td>sub-05/ses-02/func/sub-05_ses-02_task-nback_ru...</td>
      <td>sub-05_ses-02_task-nback_run-01_bold.nii</td>
      <td>05</td>
      <td>02</td>
      <td>nback</td>
      <td>01</td>
      <td>bold</td>
      <td>func</td>
      <td>.nii</td>
      <td>{}</td>
      <td>age=42; sex=M</td>
    </tr>
    <tr>
      <th>15</th>
      <td>/tmp/bids-examples/synthetic/sub-05/ses-01/fun...</td>
      <td>sub-05/ses-01/func/sub-05_ses-01_task-nback_ru...</td>
      <td>sub-05_ses-01_task-nback_run-02_bold.nii</td>
      <td>05</td>
      <td>01</td>
      <td>nback</td>
      <td>02</td>
      <td>bold</td>
      <td>func</td>
      <td>.nii</td>
      <td>{}</td>
      <td>age=42; sex=M</td>
    </tr>
    <tr>
      <th>16</th>
      <td>/tmp/bids-examples/synthetic/sub-05/ses-01/fun...</td>
      <td>sub-05/ses-01/func/sub-05_ses-01_task-rest_bol...</td>
      <td>sub-05_ses-01_task-rest_bold.nii</td>
      <td>05</td>
      <td>01</td>
      <td>rest</td>
      <td>NaN</td>
      <td>bold</td>
      <td>func</td>
      <td>.nii</td>
      <td>{}</td>
      <td>age=42; sex=M</td>
    </tr>
    <tr>
      <th>17</th>
      <td>/tmp/bids-examples/synthetic/sub-05/ses-01/fun...</td>
      <td>sub-05/ses-01/func/sub-05_ses-01_task-nback_ru...</td>
      <td>sub-05_ses-01_task-nback_run-01_bold.nii</td>
      <td>05</td>
      <td>01</td>
      <td>nback</td>
      <td>01</td>
      <td>bold</td>
      <td>func</td>
      <td>.nii</td>
      <td>{}</td>
      <td>age=42; sex=M</td>
    </tr>
    <tr>
      <th>18</th>
      <td>/tmp/bids-examples/synthetic/sub-02/ses-02/fun...</td>
      <td>sub-02/ses-02/func/sub-02_ses-02_task-rest_bol...</td>
      <td>sub-02_ses-02_task-rest_bold.nii</td>
      <td>02</td>
      <td>02</td>
      <td>rest</td>
      <td>NaN</td>
      <td>bold</td>
      <td>func</td>
      <td>.nii</td>
      <td>{}</td>
      <td>age=38; sex=M</td>
    </tr>
    <tr>
      <th>19</th>
      <td>/tmp/bids-examples/synthetic/sub-02/ses-02/fun...</td>
      <td>sub-02/ses-02/func/sub-02_ses-02_task-nback_ru...</td>
      <td>sub-02_ses-02_task-nback_run-02_bold.nii</td>
      <td>02</td>
      <td>02</td>
      <td>nback</td>
      <td>02</td>
      <td>bold</td>
      <td>func</td>
      <td>.nii</td>
      <td>{}</td>
      <td>age=38; sex=M</td>
    </tr>
    <tr>
      <th>20</th>
      <td>/tmp/bids-examples/synthetic/sub-02/ses-02/fun...</td>
      <td>sub-02/ses-02/func/sub-02_ses-02_task-nback_ru...</td>
      <td>sub-02_ses-02_task-nback_run-01_bold.nii</td>
      <td>02</td>
      <td>02</td>
      <td>nback</td>
      <td>01</td>
      <td>bold</td>
      <td>func</td>
      <td>.nii</td>
      <td>{}</td>
      <td>age=38; sex=M</td>
    </tr>
    <tr>
      <th>21</th>
      <td>/tmp/bids-examples/synthetic/sub-02/ses-01/fun...</td>
      <td>sub-02/ses-01/func/sub-02_ses-01_task-nback_ru...</td>
      <td>sub-02_ses-01_task-nback_run-02_bold.nii</td>
      <td>02</td>
      <td>01</td>
      <td>nback</td>
      <td>02</td>
      <td>bold</td>
      <td>func</td>
      <td>.nii</td>
      <td>{}</td>
      <td>age=38; sex=M</td>
    </tr>
    <tr>
      <th>22</th>
      <td>/tmp/bids-examples/synthetic/sub-02/ses-01/fun...</td>
      <td>sub-02/ses-01/func/sub-02_ses-01_task-nback_ru...</td>
      <td>sub-02_ses-01_task-nback_run-01_bold.nii</td>
      <td>02</td>
      <td>01</td>
      <td>nback</td>
      <td>01</td>
      <td>bold</td>
      <td>func</td>
      <td>.nii</td>
      <td>{}</td>
      <td>age=38; sex=M</td>
    </tr>
    <tr>
      <th>23</th>
      <td>/tmp/bids-examples/synthetic/sub-02/ses-01/fun...</td>
      <td>sub-02/ses-01/func/sub-02_ses-01_task-rest_bol...</td>
      <td>sub-02_ses-01_task-rest_bold.nii</td>
      <td>02</td>
      <td>01</td>
      <td>rest</td>
      <td>NaN</td>
      <td>bold</td>
      <td>func</td>
      <td>.nii</td>
      <td>{}</td>
      <td>age=38; sex=M</td>
    </tr>
    <tr>
      <th>24</th>
      <td>/tmp/bids-examples/synthetic/sub-03/ses-02/fun...</td>
      <td>sub-03/ses-02/func/sub-03_ses-02_task-nback_ru...</td>
      <td>sub-03_ses-02_task-nback_run-01_bold.nii</td>
      <td>03</td>
      <td>02</td>
      <td>nback</td>
      <td>01</td>
      <td>bold</td>
      <td>func</td>
      <td>.nii</td>
      <td>{}</td>
      <td>age=22; sex=M</td>
    </tr>
    <tr>
      <th>25</th>
      <td>/tmp/bids-examples/synthetic/sub-03/ses-02/fun...</td>
      <td>sub-03/ses-02/func/sub-03_ses-02_task-nback_ru...</td>
      <td>sub-03_ses-02_task-nback_run-02_bold.nii</td>
      <td>03</td>
      <td>02</td>
      <td>nback</td>
      <td>02</td>
      <td>bold</td>
      <td>func</td>
      <td>.nii</td>
      <td>{}</td>
      <td>age=22; sex=M</td>
    </tr>
    <tr>
      <th>26</th>
      <td>/tmp/bids-examples/synthetic/sub-03/ses-02/fun...</td>
      <td>sub-03/ses-02/func/sub-03_ses-02_task-rest_bol...</td>
      <td>sub-03_ses-02_task-rest_bold.nii</td>
      <td>03</td>
      <td>02</td>
      <td>rest</td>
      <td>NaN</td>
      <td>bold</td>
      <td>func</td>
      <td>.nii</td>
      <td>{}</td>
      <td>age=22; sex=M</td>
    </tr>
    <tr>
      <th>27</th>
      <td>/tmp/bids-examples/synthetic/sub-03/ses-01/fun...</td>
      <td>sub-03/ses-01/func/sub-03_ses-01_task-rest_bol...</td>
      <td>sub-03_ses-01_task-rest_bold.nii</td>
      <td>03</td>
      <td>01</td>
      <td>rest</td>
      <td>NaN</td>
      <td>bold</td>
      <td>func</td>
      <td>.nii</td>
      <td>{}</td>
      <td>age=22; sex=M</td>
    </tr>
    <tr>
      <th>28</th>
      <td>/tmp/bids-examples/synthetic/sub-03/ses-01/fun...</td>
      <td>sub-03/ses-01/func/sub-03_ses-01_task-nback_ru...</td>
      <td>sub-03_ses-01_task-nback_run-02_bold.nii</td>
      <td>03</td>
      <td>01</td>
      <td>nback</td>
      <td>02</td>
      <td>bold</td>
      <td>func</td>
      <td>.nii</td>
      <td>{}</td>
      <td>age=22; sex=M</td>
    </tr>
    <tr>
      <th>29</th>
      <td>/tmp/bids-examples/synthetic/sub-03/ses-01/fun...</td>
      <td>sub-03/ses-01/func/sub-03_ses-01_task-nback_ru...</td>
      <td>sub-03_ses-01_task-nback_run-01_bold.nii</td>
      <td>03</td>
      <td>01</td>
      <td>nback</td>
      <td>01</td>
      <td>bold</td>
      <td>func</td>
      <td>.nii</td>
      <td>{}</td>
      <td>age=22; sex=M</td>
    </tr>
  </tbody>
</table>
</div>



### Using WHERE Clause

For more SQL-like queries, you can use the WHERE clause:


```python
q.run_query("WHERE sub=01 AND datatype=func", format="dataframe")
```




<div>
<style scoped>
    .dataframe tbody tr th:only-of-type {
        vertical-align: middle;
    }

    .dataframe tbody tr th {
        vertical-align: top;
    }

    .dataframe thead th {
        text-align: right;
    }
</style>
<table border="1" class="dataframe">
  <thead>
    <tr style="text-align: right;">
      <th></th>
      <th>filepath</th>
      <th>relative_path</th>
      <th>filename</th>
      <th>sub</th>
      <th>ses</th>
      <th>task</th>
      <th>run</th>
      <th>suffix</th>
      <th>datatype</th>
      <th>extension</th>
      <th>metadata</th>
      <th>participants</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <th>0</th>
      <td>/tmp/bids-examples/synthetic/sub-01/ses-02/fun...</td>
      <td>sub-01/ses-02/func/sub-01_ses-02_task-nback_ru...</td>
      <td>sub-01_ses-02_task-nback_run-02_bold.nii</td>
      <td>01</td>
      <td>02</td>
      <td>nback</td>
      <td>02</td>
      <td>bold</td>
      <td>func</td>
      <td>.nii</td>
      <td>{}</td>
      <td>age=34; sex=F</td>
    </tr>
    <tr>
      <th>1</th>
      <td>/tmp/bids-examples/synthetic/sub-01/ses-02/fun...</td>
      <td>sub-01/ses-02/func/sub-01_ses-02_task-nback_ru...</td>
      <td>sub-01_ses-02_task-nback_run-01_bold.nii</td>
      <td>01</td>
      <td>02</td>
      <td>nback</td>
      <td>01</td>
      <td>bold</td>
      <td>func</td>
      <td>.nii</td>
      <td>{}</td>
      <td>age=34; sex=F</td>
    </tr>
    <tr>
      <th>2</th>
      <td>/tmp/bids-examples/synthetic/sub-01/ses-02/fun...</td>
      <td>sub-01/ses-02/func/sub-01_ses-02_task-rest_bol...</td>
      <td>sub-01_ses-02_task-rest_bold.nii</td>
      <td>01</td>
      <td>02</td>
      <td>rest</td>
      <td>NaN</td>
      <td>bold</td>
      <td>func</td>
      <td>.nii</td>
      <td>{}</td>
      <td>age=34; sex=F</td>
    </tr>
    <tr>
      <th>3</th>
      <td>/tmp/bids-examples/synthetic/sub-01/ses-01/fun...</td>
      <td>sub-01/ses-01/func/sub-01_ses-01_task-nback_ru...</td>
      <td>sub-01_ses-01_task-nback_run-02_bold.nii</td>
      <td>01</td>
      <td>01</td>
      <td>nback</td>
      <td>02</td>
      <td>bold</td>
      <td>func</td>
      <td>.nii</td>
      <td>{}</td>
      <td>age=34; sex=F</td>
    </tr>
    <tr>
      <th>4</th>
      <td>/tmp/bids-examples/synthetic/sub-01/ses-01/fun...</td>
      <td>sub-01/ses-01/func/sub-01_ses-01_task-rest_bol...</td>
      <td>sub-01_ses-01_task-rest_bold.nii</td>
      <td>01</td>
      <td>01</td>
      <td>rest</td>
      <td>NaN</td>
      <td>bold</td>
      <td>func</td>
      <td>.nii</td>
      <td>{}</td>
      <td>age=34; sex=F</td>
    </tr>
    <tr>
      <th>5</th>
      <td>/tmp/bids-examples/synthetic/sub-01/ses-01/fun...</td>
      <td>sub-01/ses-01/func/sub-01_ses-01_task-nback_ru...</td>
      <td>sub-01_ses-01_task-nback_run-01_bold.nii</td>
      <td>01</td>
      <td>01</td>
      <td>nback</td>
      <td>01</td>
      <td>bold</td>
      <td>func</td>
      <td>.nii</td>
      <td>{}</td>
      <td>age=34; sex=F</td>
    </tr>
  </tbody>
</table>
</div>



## Part 2: SELECT Clause and Field Selection

By default, BIQL returns all available fields. Use SELECT to choose specific fields:


```python
q.run_query(
    "SELECT sub, task, run, filename WHERE datatype=func",
    format="dataframe"
)
```




<div>
<style scoped>
    .dataframe tbody tr th:only-of-type {
        vertical-align: middle;
    }

    .dataframe tbody tr th {
        vertical-align: top;
    }

    .dataframe thead th {
        text-align: right;
    }
</style>
<table border="1" class="dataframe">
  <thead>
    <tr style="text-align: right;">
      <th></th>
      <th>sub</th>
      <th>task</th>
      <th>run</th>
      <th>filename</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <th>0</th>
      <td>01</td>
      <td>nback</td>
      <td>02</td>
      <td>sub-01_ses-02_task-nback_run-02_bold.nii</td>
    </tr>
    <tr>
      <th>1</th>
      <td>01</td>
      <td>nback</td>
      <td>01</td>
      <td>sub-01_ses-02_task-nback_run-01_bold.nii</td>
    </tr>
    <tr>
      <th>2</th>
      <td>01</td>
      <td>rest</td>
      <td>None</td>
      <td>sub-01_ses-02_task-rest_bold.nii</td>
    </tr>
    <tr>
      <th>3</th>
      <td>01</td>
      <td>nback</td>
      <td>02</td>
      <td>sub-01_ses-01_task-nback_run-02_bold.nii</td>
    </tr>
    <tr>
      <th>4</th>
      <td>01</td>
      <td>rest</td>
      <td>None</td>
      <td>sub-01_ses-01_task-rest_bold.nii</td>
    </tr>
    <tr>
      <th>5</th>
      <td>01</td>
      <td>nback</td>
      <td>01</td>
      <td>sub-01_ses-01_task-nback_run-01_bold.nii</td>
    </tr>
    <tr>
      <th>6</th>
      <td>04</td>
      <td>nback</td>
      <td>02</td>
      <td>sub-04_ses-02_task-nback_run-02_bold.nii</td>
    </tr>
    <tr>
      <th>7</th>
      <td>04</td>
      <td>nback</td>
      <td>01</td>
      <td>sub-04_ses-02_task-nback_run-01_bold.nii</td>
    </tr>
    <tr>
      <th>8</th>
      <td>04</td>
      <td>rest</td>
      <td>None</td>
      <td>sub-04_ses-02_task-rest_bold.nii</td>
    </tr>
    <tr>
      <th>9</th>
      <td>04</td>
      <td>nback</td>
      <td>02</td>
      <td>sub-04_ses-01_task-nback_run-02_bold.nii</td>
    </tr>
    <tr>
      <th>10</th>
      <td>04</td>
      <td>rest</td>
      <td>None</td>
      <td>sub-04_ses-01_task-rest_bold.nii</td>
    </tr>
    <tr>
      <th>11</th>
      <td>04</td>
      <td>nback</td>
      <td>01</td>
      <td>sub-04_ses-01_task-nback_run-01_bold.nii</td>
    </tr>
    <tr>
      <th>12</th>
      <td>05</td>
      <td>rest</td>
      <td>None</td>
      <td>sub-05_ses-02_task-rest_bold.nii</td>
    </tr>
    <tr>
      <th>13</th>
      <td>05</td>
      <td>nback</td>
      <td>02</td>
      <td>sub-05_ses-02_task-nback_run-02_bold.nii</td>
    </tr>
    <tr>
      <th>14</th>
      <td>05</td>
      <td>nback</td>
      <td>01</td>
      <td>sub-05_ses-02_task-nback_run-01_bold.nii</td>
    </tr>
    <tr>
      <th>15</th>
      <td>05</td>
      <td>nback</td>
      <td>02</td>
      <td>sub-05_ses-01_task-nback_run-02_bold.nii</td>
    </tr>
    <tr>
      <th>16</th>
      <td>05</td>
      <td>rest</td>
      <td>None</td>
      <td>sub-05_ses-01_task-rest_bold.nii</td>
    </tr>
    <tr>
      <th>17</th>
      <td>05</td>
      <td>nback</td>
      <td>01</td>
      <td>sub-05_ses-01_task-nback_run-01_bold.nii</td>
    </tr>
    <tr>
      <th>18</th>
      <td>02</td>
      <td>rest</td>
      <td>None</td>
      <td>sub-02_ses-02_task-rest_bold.nii</td>
    </tr>
    <tr>
      <th>19</th>
      <td>02</td>
      <td>nback</td>
      <td>02</td>
      <td>sub-02_ses-02_task-nback_run-02_bold.nii</td>
    </tr>
    <tr>
      <th>20</th>
      <td>02</td>
      <td>nback</td>
      <td>01</td>
      <td>sub-02_ses-02_task-nback_run-01_bold.nii</td>
    </tr>
    <tr>
      <th>21</th>
      <td>02</td>
      <td>nback</td>
      <td>02</td>
      <td>sub-02_ses-01_task-nback_run-02_bold.nii</td>
    </tr>
    <tr>
      <th>22</th>
      <td>02</td>
      <td>nback</td>
      <td>01</td>
      <td>sub-02_ses-01_task-nback_run-01_bold.nii</td>
    </tr>
    <tr>
      <th>23</th>
      <td>02</td>
      <td>rest</td>
      <td>None</td>
      <td>sub-02_ses-01_task-rest_bold.nii</td>
    </tr>
    <tr>
      <th>24</th>
      <td>03</td>
      <td>nback</td>
      <td>01</td>
      <td>sub-03_ses-02_task-nback_run-01_bold.nii</td>
    </tr>
    <tr>
      <th>25</th>
      <td>03</td>
      <td>nback</td>
      <td>02</td>
      <td>sub-03_ses-02_task-nback_run-02_bold.nii</td>
    </tr>
    <tr>
      <th>26</th>
      <td>03</td>
      <td>rest</td>
      <td>None</td>
      <td>sub-03_ses-02_task-rest_bold.nii</td>
    </tr>
    <tr>
      <th>27</th>
      <td>03</td>
      <td>rest</td>
      <td>None</td>
      <td>sub-03_ses-01_task-rest_bold.nii</td>
    </tr>
    <tr>
      <th>28</th>
      <td>03</td>
      <td>nback</td>
      <td>02</td>
      <td>sub-03_ses-01_task-nback_run-02_bold.nii</td>
    </tr>
    <tr>
      <th>29</th>
      <td>03</td>
      <td>nback</td>
      <td>01</td>
      <td>sub-03_ses-01_task-nback_run-01_bold.nii</td>
    </tr>
  </tbody>
</table>
</div>




```python
q.run_query(
    "SELECT sub, relative_path WHERE suffix=T1w",
    format="dataframe"
)
```




<div>
<style scoped>
    .dataframe tbody tr th:only-of-type {
        vertical-align: middle;
    }

    .dataframe tbody tr th {
        vertical-align: top;
    }

    .dataframe thead th {
        text-align: right;
    }
</style>
<table border="1" class="dataframe">
  <thead>
    <tr style="text-align: right;">
      <th></th>
      <th>sub</th>
      <th>relative_path</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <th>0</th>
      <td>01</td>
      <td>sub-01/ses-02/anat/sub-01_ses-02_T1w.nii</td>
    </tr>
    <tr>
      <th>1</th>
      <td>01</td>
      <td>sub-01/ses-01/anat/sub-01_ses-01_T1w.nii</td>
    </tr>
    <tr>
      <th>2</th>
      <td>04</td>
      <td>sub-04/ses-02/anat/sub-04_ses-02_T1w.nii</td>
    </tr>
    <tr>
      <th>3</th>
      <td>04</td>
      <td>sub-04/ses-01/anat/sub-04_ses-01_T1w.nii</td>
    </tr>
    <tr>
      <th>4</th>
      <td>05</td>
      <td>sub-05/ses-02/anat/sub-05_ses-02_T1w.nii</td>
    </tr>
    <tr>
      <th>5</th>
      <td>05</td>
      <td>sub-05/ses-01/anat/sub-05_ses-01_T1w.nii</td>
    </tr>
    <tr>
      <th>6</th>
      <td>02</td>
      <td>sub-02/ses-02/anat/sub-02_ses-02_T1w.nii</td>
    </tr>
    <tr>
      <th>7</th>
      <td>02</td>
      <td>sub-02/ses-01/anat/sub-02_ses-01_T1w.nii</td>
    </tr>
    <tr>
      <th>8</th>
      <td>03</td>
      <td>sub-03/ses-02/anat/sub-03_ses-02_T1w.nii</td>
    </tr>
    <tr>
      <th>9</th>
      <td>03</td>
      <td>sub-03/ses-01/anat/sub-03_ses-01_T1w.nii</td>
    </tr>
  </tbody>
</table>
</div>



## Part 3: Pattern Matching

BIQL supports wildcards and regular expressions for flexible matching:


```python
results = q.run_query("suffix=*bold*")
len(results)  # Count of files with 'bold' in suffix
```




    30




```python
q.run_query(
    "SELECT DISTINCT task WHERE task~=\".*back.*\"",
    format="dataframe"
)
```




<div>
<style scoped>
    .dataframe tbody tr th:only-of-type {
        vertical-align: middle;
    }

    .dataframe tbody tr th {
        vertical-align: top;
    }

    .dataframe thead th {
        text-align: right;
    }
</style>
<table border="1" class="dataframe">
  <thead>
    <tr style="text-align: right;">
      <th></th>
      <th>task</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <th>0</th>
      <td>nback</td>
    </tr>
  </tbody>
</table>
</div>



## Part 4: Ranges and Lists

BIQL supports range queries and IN operators for matching multiple values:


```python
q.run_query(
    "SELECT sub, ARRAY_AGG(DISTINCT task) as tasks, COUNT(*) as total_files "
    "WHERE sub IN ['01', '02', '03'] "
    "GROUP BY sub",
    format="json"
)
```




    [{'sub': '01', 'tasks': ['nback', 'rest', 'stroop'], 'total_files': 12},
     {'sub': '02', 'tasks': ['nback', 'rest', 'stroop'], 'total_files': 12},
     {'sub': '03', 'tasks': ['nback', 'rest', 'stroop'], 'total_files': 12}]




```python
q.run_query(
    "SELECT task, run, COUNT(*) as file_count, "
    "COUNT(DISTINCT sub) as subjects "
    "WHERE datatype=func "
    "GROUP BY task, run "
    "ORDER BY task, run",
    format="dataframe"
)
```




<div>
<style scoped>
    .dataframe tbody tr th:only-of-type {
        vertical-align: middle;
    }

    .dataframe tbody tr th {
        vertical-align: top;
    }

    .dataframe thead th {
        text-align: right;
    }
</style>
<table border="1" class="dataframe">
  <thead>
    <tr style="text-align: right;">
      <th></th>
      <th>task</th>
      <th>run</th>
      <th>file_count</th>
      <th>subjects</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <th>0</th>
      <td>nback</td>
      <td>01</td>
      <td>10</td>
      <td>5</td>
    </tr>
    <tr>
      <th>1</th>
      <td>nback</td>
      <td>02</td>
      <td>10</td>
      <td>5</td>
    </tr>
    <tr>
      <th>2</th>
      <td>rest</td>
      <td>None</td>
      <td>10</td>
      <td>5</td>
    </tr>
  </tbody>
</table>
</div>



## Part 5: Grouping and Aggregation

BIQL supports SQL-like grouping and aggregation functions:


```python
q.run_query("SELECT sub, COUNT(*) GROUP BY sub", format="dataframe")
```




<div>
<style scoped>
    .dataframe tbody tr th:only-of-type {
        vertical-align: middle;
    }

    .dataframe tbody tr th {
        vertical-align: top;
    }

    .dataframe thead th {
        text-align: right;
    }
</style>
<table border="1" class="dataframe">
  <thead>
    <tr style="text-align: right;">
      <th></th>
      <th>sub</th>
      <th>count</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <th>0</th>
      <td>01</td>
      <td>12</td>
    </tr>
    <tr>
      <th>1</th>
      <td>04</td>
      <td>12</td>
    </tr>
    <tr>
      <th>2</th>
      <td>05</td>
      <td>12</td>
    </tr>
    <tr>
      <th>3</th>
      <td>02</td>
      <td>12</td>
    </tr>
    <tr>
      <th>4</th>
      <td>03</td>
      <td>12</td>
    </tr>
  </tbody>
</table>
</div>




```python
q.run_query(
    "SELECT sub, datatype, COUNT(*) GROUP BY sub, datatype",
    format="json"
)
```




    [{'sub': '01', 'datatype': 'anat', 'count': 2},
     {'sub': '01', 'datatype': 'func', 'count': 6},
     {'sub': '04', 'datatype': 'anat', 'count': 2},
     {'sub': '04', 'datatype': 'func', 'count': 6},
     {'sub': '05', 'datatype': 'anat', 'count': 2},
     {'sub': '05', 'datatype': 'func', 'count': 6},
     {'sub': '02', 'datatype': 'anat', 'count': 2},
     {'sub': '02', 'datatype': 'func', 'count': 6},
     {'sub': '03', 'datatype': 'anat', 'count': 2},
     {'sub': '03', 'datatype': 'func', 'count': 6},
     {'sub': '01', 'datatype': None, 'count': 3},
     {'sub': '01', 'datatype': 'beh', 'count': 1},
     {'sub': '04', 'datatype': None, 'count': 3},
     {'sub': '04', 'datatype': 'beh', 'count': 1},
     {'sub': '05', 'datatype': None, 'count': 3},
     {'sub': '05', 'datatype': 'beh', 'count': 1},
     {'sub': '02', 'datatype': None, 'count': 3},
     {'sub': '02', 'datatype': 'beh', 'count': 1},
     {'sub': '03', 'datatype': None, 'count': 3},
     {'sub': '03', 'datatype': 'beh', 'count': 1}]



## Part 6: Working with Metadata

BIQL can query JSON sidecar metadata using the `metadata.` namespace.
The synthetic dataset has task-level metadata files like `task-nback_bold.json`:


```python
q.run_query(
    "SELECT task, COUNT(*) as file_count, "
    "ARRAY_AGG(DISTINCT sub) as subjects_with_task, "
    "ARRAY_AGG(DISTINCT datatype) as datatypes "
    "GROUP BY task",
    format="json"
)
```




    [{'task': None,
      'file_count': 25,
      'subjects_with_task': ['01', '02', '03', '04', '05'],
      'datatypes': ['anat']},
     {'task': 'nback',
      'file_count': 20,
      'subjects_with_task': ['01', '02', '03', '04', '05'],
      'datatypes': ['func']},
     {'task': 'rest',
      'file_count': 10,
      'subjects_with_task': ['01', '02', '03', '04', '05'],
      'datatypes': ['func']},
     {'task': 'stroop',
      'file_count': 5,
      'subjects_with_task': ['01', '02', '03', '04', '05'],
      'datatypes': ['beh']}]




```python
q.run_query(
    "SELECT datatype, COUNT(*) as total_files, "
    "COUNT(DISTINCT sub) as subjects, "
    "ARRAY_AGG(DISTINCT sub) as subject_list "
    "GROUP BY datatype "
    "ORDER BY total_files DESC",
    format="json"
)
```




    [{'datatype': 'anat',
      'total_files': 10,
      'subjects': 5,
      'subject_list': ['01', '02', '03', '04', '05']},
     {'datatype': 'func',
      'total_files': 30,
      'subjects': 5,
      'subject_list': ['01', '02', '03', '04', '05']},
     {'datatype': None,
      'total_files': 15,
      'subjects': 5,
      'subject_list': ['01', '02', '03', '04', '05']},
     {'datatype': 'beh',
      'total_files': 5,
      'subjects': 5,
      'subject_list': ['01', '02', '03', '04', '05']}]



## Part 7: Participant Information

Access participant demographics using the `participants.` namespace:


```python
q.run_query(
    "SELECT DISTINCT sub, participants.age, participants.sex",
    format="dataframe"
)
```




<div>
<style scoped>
    .dataframe tbody tr th:only-of-type {
        vertical-align: middle;
    }

    .dataframe tbody tr th {
        vertical-align: top;
    }

    .dataframe thead th {
        text-align: right;
    }
</style>
<table border="1" class="dataframe">
  <thead>
    <tr style="text-align: right;">
      <th></th>
      <th>sub</th>
      <th>participants.age</th>
      <th>participants.sex</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <th>0</th>
      <td>01</td>
      <td>34</td>
      <td>F</td>
    </tr>
    <tr>
      <th>1</th>
      <td>04</td>
      <td>21</td>
      <td>F</td>
    </tr>
    <tr>
      <th>2</th>
      <td>05</td>
      <td>42</td>
      <td>M</td>
    </tr>
    <tr>
      <th>3</th>
      <td>02</td>
      <td>38</td>
      <td>M</td>
    </tr>
    <tr>
      <th>4</th>
      <td>03</td>
      <td>22</td>
      <td>M</td>
    </tr>
  </tbody>
</table>
</div>




```python
q.run_query(
    "SELECT sub, task, participants.age WHERE participants.age > 25",
    format="dataframe"
)
```




<div>
<style scoped>
    .dataframe tbody tr th:only-of-type {
        vertical-align: middle;
    }

    .dataframe tbody tr th {
        vertical-align: top;
    }

    .dataframe thead th {
        text-align: right;
    }
</style>
<table border="1" class="dataframe">
  <thead>
    <tr style="text-align: right;">
      <th></th>
      <th>sub</th>
      <th>task</th>
      <th>participants.age</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <th>0</th>
      <td>01</td>
      <td>None</td>
      <td>34</td>
    </tr>
    <tr>
      <th>1</th>
      <td>01</td>
      <td>nback</td>
      <td>34</td>
    </tr>
    <tr>
      <th>2</th>
      <td>01</td>
      <td>nback</td>
      <td>34</td>
    </tr>
    <tr>
      <th>3</th>
      <td>01</td>
      <td>rest</td>
      <td>34</td>
    </tr>
    <tr>
      <th>4</th>
      <td>01</td>
      <td>None</td>
      <td>34</td>
    </tr>
    <tr>
      <th>5</th>
      <td>01</td>
      <td>nback</td>
      <td>34</td>
    </tr>
    <tr>
      <th>6</th>
      <td>01</td>
      <td>rest</td>
      <td>34</td>
    </tr>
    <tr>
      <th>7</th>
      <td>01</td>
      <td>nback</td>
      <td>34</td>
    </tr>
    <tr>
      <th>8</th>
      <td>05</td>
      <td>None</td>
      <td>42</td>
    </tr>
    <tr>
      <th>9</th>
      <td>05</td>
      <td>rest</td>
      <td>42</td>
    </tr>
    <tr>
      <th>10</th>
      <td>05</td>
      <td>nback</td>
      <td>42</td>
    </tr>
    <tr>
      <th>11</th>
      <td>05</td>
      <td>nback</td>
      <td>42</td>
    </tr>
    <tr>
      <th>12</th>
      <td>05</td>
      <td>None</td>
      <td>42</td>
    </tr>
    <tr>
      <th>13</th>
      <td>05</td>
      <td>nback</td>
      <td>42</td>
    </tr>
    <tr>
      <th>14</th>
      <td>05</td>
      <td>rest</td>
      <td>42</td>
    </tr>
    <tr>
      <th>15</th>
      <td>05</td>
      <td>nback</td>
      <td>42</td>
    </tr>
    <tr>
      <th>16</th>
      <td>02</td>
      <td>None</td>
      <td>38</td>
    </tr>
    <tr>
      <th>17</th>
      <td>02</td>
      <td>rest</td>
      <td>38</td>
    </tr>
    <tr>
      <th>18</th>
      <td>02</td>
      <td>nback</td>
      <td>38</td>
    </tr>
    <tr>
      <th>19</th>
      <td>02</td>
      <td>nback</td>
      <td>38</td>
    </tr>
    <tr>
      <th>20</th>
      <td>02</td>
      <td>None</td>
      <td>38</td>
    </tr>
    <tr>
      <th>21</th>
      <td>02</td>
      <td>nback</td>
      <td>38</td>
    </tr>
    <tr>
      <th>22</th>
      <td>02</td>
      <td>nback</td>
      <td>38</td>
    </tr>
    <tr>
      <th>23</th>
      <td>02</td>
      <td>rest</td>
      <td>38</td>
    </tr>
    <tr>
      <th>24</th>
      <td>01</td>
      <td>None</td>
      <td>34</td>
    </tr>
    <tr>
      <th>25</th>
      <td>01</td>
      <td>None</td>
      <td>34</td>
    </tr>
    <tr>
      <th>26</th>
      <td>01</td>
      <td>None</td>
      <td>34</td>
    </tr>
    <tr>
      <th>27</th>
      <td>01</td>
      <td>stroop</td>
      <td>34</td>
    </tr>
    <tr>
      <th>28</th>
      <td>05</td>
      <td>None</td>
      <td>42</td>
    </tr>
    <tr>
      <th>29</th>
      <td>05</td>
      <td>None</td>
      <td>42</td>
    </tr>
    <tr>
      <th>30</th>
      <td>05</td>
      <td>None</td>
      <td>42</td>
    </tr>
    <tr>
      <th>31</th>
      <td>05</td>
      <td>stroop</td>
      <td>42</td>
    </tr>
    <tr>
      <th>32</th>
      <td>02</td>
      <td>None</td>
      <td>38</td>
    </tr>
    <tr>
      <th>33</th>
      <td>02</td>
      <td>None</td>
      <td>38</td>
    </tr>
    <tr>
      <th>34</th>
      <td>02</td>
      <td>None</td>
      <td>38</td>
    </tr>
    <tr>
      <th>35</th>
      <td>02</td>
      <td>stroop</td>
      <td>38</td>
    </tr>
  </tbody>
</table>
</div>



## Part 8: Advanced Queries

Let's combine multiple features for more complex queries:


```python
q.run_query("""
    SELECT sub, ses, task, COUNT(*) as n_runs
    WHERE datatype=func AND task != rest
    GROUP BY sub, ses, task
    HAVING COUNT(*) > 1
    ORDER BY sub, task
""", format="json")
```




    [{'sub': '01', 'ses': '02', 'task': 'nback', 'n_runs': 2},
     {'sub': '01', 'ses': '01', 'task': 'nback', 'n_runs': 2},
     {'sub': '02', 'ses': '02', 'task': 'nback', 'n_runs': 2},
     {'sub': '02', 'ses': '01', 'task': 'nback', 'n_runs': 2},
     {'sub': '03', 'ses': '02', 'task': 'nback', 'n_runs': 2},
     {'sub': '03', 'ses': '01', 'task': 'nback', 'n_runs': 2},
     {'sub': '04', 'ses': '02', 'task': 'nback', 'n_runs': 2},
     {'sub': '04', 'ses': '01', 'task': 'nback', 'n_runs': 2},
     {'sub': '05', 'ses': '02', 'task': 'nback', 'n_runs': 2},
     {'sub': '05', 'ses': '01', 'task': 'nback', 'n_runs': 2}]




```python
q.run_query("""
    SELECT sub, task,
           ARRAY_AGG(filename WHERE suffix='bold') as imaging_files,
           ARRAY_AGG(filename WHERE run='01') as run01_files,
           ARRAY_AGG(filename WHERE run='02') as run02_files
    WHERE datatype=func
    GROUP BY sub, task
""", format="table")  # Using table format since arrays don't display well in dataframes
```




    '| imaging_files   | run01_files     | run02_files     | sub | task  |\n| --------------- | --------------- | --------------- | --- | ----- |\n| [...4 items...] | [...2 items...] | [...2 items...] | 01  | nback |\n| [...2 items...] | [...0 items...] | [...0 items...] | 01  | rest  |\n| [...4 items...] | [...2 items...] | [...2 items...] | 04  | nback |\n| [...2 items...] | [...0 items...] | [...0 items...] | 04  | rest  |\n| [...2 items...] | [...0 items...] | [...0 items...] | 05  | rest  |\n| [...4 items...] | [...2 items...] | [...2 items...] | 05  | nback |\n| [...2 items...] | [...0 items...] | [...0 items...] | 02  | rest  |\n| [...4 items...] | [...2 items...] | [...2 items...] | 02  | nback |\n| [...4 items...] | [...2 items...] | [...2 items...] | 03  | nback |\n| [...2 items...] | [...0 items...] | [...0 items...] | 03  | rest  |'



## Part 9: Output Formats

BIQL supports multiple output formats for different use cases:


```python
sample_query = "SELECT sub, task, run WHERE datatype=func AND sub=01"

print(q.run_query(sample_query, format="table"))
```

    | run | sub | task  |
    | --- | --- | ----- |
    | 02  | 01  | nback |
    | 01  | 01  | nback |
    |     | 01  | rest  |
    | 02  | 01  | nback |
    |     | 01  | rest  |
    | 01  | 01  | nback |



```python
print(q.run_query(sample_query, format="csv"))
```

    run,sub,task
    02,01,nback
    01,01,nback
    ,01,rest
    02,01,nback
    ,01,rest
    01,01,nback
    



```python
results_json = q.run_query(sample_query, format="json")
results_json[:2]  # Show first 2 entries
```




    [{'sub': '01', 'task': 'nback', 'run': '02'},
     {'sub': '01', 'task': 'nback', 'run': '01'}]




```python
print(q.run_query("WHERE sub=01 AND suffix=T1w", format="paths"))
```

    /tmp/bids-examples/synthetic/sub-01/ses-02/anat/sub-01_ses-02_T1w.nii
    /tmp/bids-examples/synthetic/sub-01/ses-01/anat/sub-01_ses-01_T1w.nii



```python
q.run_query(sample_query, format="dataframe")
```




<div>
<style scoped>
    .dataframe tbody tr th:only-of-type {
        vertical-align: middle;
    }

    .dataframe tbody tr th {
        vertical-align: top;
    }

    .dataframe thead th {
        text-align: right;
    }
</style>
<table border="1" class="dataframe">
  <thead>
    <tr style="text-align: right;">
      <th></th>
      <th>sub</th>
      <th>task</th>
      <th>run</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <th>0</th>
      <td>01</td>
      <td>nback</td>
      <td>02</td>
    </tr>
    <tr>
      <th>1</th>
      <td>01</td>
      <td>nback</td>
      <td>01</td>
    </tr>
    <tr>
      <th>2</th>
      <td>01</td>
      <td>rest</td>
      <td>None</td>
    </tr>
    <tr>
      <th>3</th>
      <td>01</td>
      <td>nback</td>
      <td>02</td>
    </tr>
    <tr>
      <th>4</th>
      <td>01</td>
      <td>rest</td>
      <td>None</td>
    </tr>
    <tr>
      <th>5</th>
      <td>01</td>
      <td>nback</td>
      <td>01</td>
    </tr>
  </tbody>
</table>
</div>



## Part 10: Real-World Examples

Let's look at some practical queries you might use in neuroimaging research:


```python
q.run_query("""
    SELECT sub, 
           COUNT(*) as total_files,
           COUNT(DISTINCT datatype) as datatypes,
           ARRAY_AGG(DISTINCT datatype) as available_data
    GROUP BY sub
""", format="json")
```




    [{'sub': '01',
      'total_files': 12,
      'datatypes': 3,
      'available_data': ['anat', 'beh', 'func']},
     {'sub': '04',
      'total_files': 12,
      'datatypes': 3,
      'available_data': ['anat', 'beh', 'func']},
     {'sub': '05',
      'total_files': 12,
      'datatypes': 3,
      'available_data': ['anat', 'beh', 'func']},
     {'sub': '02',
      'total_files': 12,
      'datatypes': 3,
      'available_data': ['anat', 'beh', 'func']},
     {'sub': '03',
      'total_files': 12,
      'datatypes': 3,
      'available_data': ['anat', 'beh', 'func']}]




```python
q.run_query("""
    SELECT sub, ses,
           COUNT(*) as files_per_session,
           ARRAY_AGG(DISTINCT task) as tasks_in_session
    GROUP BY sub, ses
""", format="json")
```




    [{'sub': '01',
      'ses': '02',
      'files_per_session': 5,
      'tasks_in_session': ['nback', 'rest']},
     {'sub': '01',
      'ses': '01',
      'files_per_session': 6,
      'tasks_in_session': ['nback', 'rest', 'stroop']},
     {'sub': '04',
      'ses': '02',
      'files_per_session': 5,
      'tasks_in_session': ['nback', 'rest']},
     {'sub': '04',
      'ses': '01',
      'files_per_session': 6,
      'tasks_in_session': ['nback', 'rest', 'stroop']},
     {'sub': '05',
      'ses': '02',
      'files_per_session': 5,
      'tasks_in_session': ['nback', 'rest']},
     {'sub': '05',
      'ses': '01',
      'files_per_session': 6,
      'tasks_in_session': ['nback', 'rest', 'stroop']},
     {'sub': '02',
      'ses': '02',
      'files_per_session': 5,
      'tasks_in_session': ['nback', 'rest']},
     {'sub': '02',
      'ses': '01',
      'files_per_session': 6,
      'tasks_in_session': ['nback', 'rest', 'stroop']},
     {'sub': '03',
      'ses': '02',
      'files_per_session': 5,
      'tasks_in_session': ['nback', 'rest']},
     {'sub': '03',
      'ses': '01',
      'files_per_session': 6,
      'tasks_in_session': ['nback', 'rest', 'stroop']},
     {'sub': '01', 'ses': None, 'files_per_session': 1, 'tasks_in_session': []},
     {'sub': '04', 'ses': None, 'files_per_session': 1, 'tasks_in_session': []},
     {'sub': '05', 'ses': None, 'files_per_session': 1, 'tasks_in_session': []},
     {'sub': '02', 'ses': None, 'files_per_session': 1, 'tasks_in_session': []},
     {'sub': '03', 'ses': None, 'files_per_session': 1, 'tasks_in_session': []}]




```python
q.run_query("""
    SELECT sub,
           COUNT(DISTINCT task) as unique_tasks,
           ARRAY_AGG(DISTINCT task) as completed_tasks,
           COUNT(*) as total_functional_files
    WHERE datatype=func
    GROUP BY sub
    HAVING COUNT(DISTINCT task) > 1  # Subjects with multiple tasks
""", format="json")
```




    [{'sub': '01',
      'unique_tasks': 2,
      'completed_tasks': ['nback', 'rest'],
      'total_functional_files': 6},
     {'sub': '04',
      'unique_tasks': 2,
      'completed_tasks': ['nback', 'rest'],
      'total_functional_files': 6},
     {'sub': '05',
      'unique_tasks': 2,
      'completed_tasks': ['nback', 'rest'],
      'total_functional_files': 6},
     {'sub': '02',
      'unique_tasks': 2,
      'completed_tasks': ['nback', 'rest'],
      'total_functional_files': 6},
     {'sub': '03',
      'unique_tasks': 2,
      'completed_tasks': ['nback', 'rest'],
      'total_functional_files': 6}]



## Summary

You've learned how to:

1. **Basic queries**: Filter by BIDS entities
2. **Logical operators**: Combine conditions with AND, OR, NOT
3. **SELECT clause**: Choose specific fields to return
4. **Pattern matching**: Use wildcards and regex
5. **Ranges and lists**: Query multiple values efficiently
6. **Aggregations**: Count and group data
7. **Metadata queries**: Access JSON sidecar information
8. **Participant data**: Query demographics
9. **Complex queries**: Combine multiple features
10. **Output formats**: Export results in different formats

## Next Steps

- Check out the [Language Reference](language.md) for complete syntax details
- Explore more [examples](../examples/) for specific use cases
- Use the CLI tool `biql` for command-line queries
- Integrate BIQL into your Python analysis pipelines

Happy querying!
