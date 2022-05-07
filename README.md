# Data-Analyst-Simulator-HWs

This repository contains projects created as part of the Data anaylist simulator course (Karpov.courses) in April 2022:

### reports_alerts/
- report_feed.py and report_both_services.py contain Python scripts for forming everyday reports of main metrics of a mock social app. This involves extracting data from a Clickhouse database, forming necessary texts and plots, and sending them into a group chat with the use of a Telegram bot.
- alerts.py contains a script for regular monitoring of key metrics and sending notifications in Telegram when anomalies are detected.

### ab_tests/
- AA_test_task.ipynb - analysis of a mock AA-test results using bootstrapping
- AB_test_task.ipynb - analysis of a mock AB-test results with a variety of methods (Mann-Whitney test, Mann-Whitney test over bucket transformation, t-test, t-test over a smoothed metric, t-test over bucket transformation, t-test over Poisson bootstrap)
- yandex_linearized_task.ipynb - analysis of a mock AB-test results using linearization

### airflow.py
Script for an ETL-pipeline executed with Airflow. Involves data extraction and transformation into a table with summary statistics of key metrics over users' age, gender and OS.

