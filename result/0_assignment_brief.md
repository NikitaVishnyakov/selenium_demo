**Automation Engineer \- Home Assignment** 

**General Guidelines** 

In this exercise, you are tested for your test planning and automation skill set. 

● Implementing with Python’s Pytest framework is required. 

● The code should be self-explanatory, well structured, and written by the selected language's code standards and the framework’s best practices. 

● You can use any 3rd party package you wish. 

● The project should be easy to run and documented. 

● You are encouraged to use any generative AI software tools. 

**Exercise Description** 

You are presented with a new REST api service that needs to be tested before release. 

The service container image can be found on docker hub at 

https://hub.docker.com/r/infralightio/test-integration-api. 

The API exposes an openAPI specification at http://localhost:8080/swagger/index.html\#/. 

The service uses Basic Authentication. 

The service is a multi tenant and must ensure tenant segregation. 

The service must uphold the openAPI specification that is exposed. 

The service must handle a load of at least 1000 requests per minute. 2 test users are pre-populated in the service: 

| UserName  | Password |
| :---- | :---- |
| test1  | test123 |
| test2  | test456 |

Your task is to: 

● Create and automate a test plan for the service. 

● Ensure that the test automation is extendable for future features. ● Generate a test report. 

● Create the automation to run the service, the test suite and produce the test report in any format you feel is appropriate.  
Success Criteria 

● All bugs are found and reported clearly 

● Proper config management (no hardcoded values, constants and enums when appropriate, parameterization, no duplicate code) 

● Usages of fixtures and reusable components 

● Clean test structure and separation of concerns 

● Proper Contract validation 

● Self-contained execution (the project should run with a single command) ● Bonus: load testing 

**Good luck\!**