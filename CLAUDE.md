# Portfolio Analytics

The goal of this project is twofold
1. Allow anyone to view their investments in a single application & build a plan for what they should do next if they are not happy
2. Teach people how to build a robust investment portfolio

This project aims to make this easy for users, even if they do not have a good understanding of personal finance, securities/securitization, capital markets or asset management. 

## How we do this
1. We ingest data from various sources to provide information to the user
2. We give the user the ability to add & explore scenarios of how they can spend their money
3. We provide education & analysis of content & their mock decisions
4. We run simulations at the users request based on historical occurences & plausible situtations that the user can come up with

## The technicals
This project is a monorepo
1. api: python based web server with a transactional postgres database
2. portfolio_analytics: dbt based datapipeline for fetching raw data & tranforming it to be used by the application
3. web: React based client application
4. docker: infrastructure & dependencies for running the full system locally

