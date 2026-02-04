#!/bin/bash
# Create the S3 bucket for portfolio analytics
awslocal s3 mb s3://portfolio-analytics
echo "Created bucket: portfolio-analytics"
