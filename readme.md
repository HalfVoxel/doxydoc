# Documentation Post-Processor for Doxygen


Doxygen is a great documentation system. It is awesome at figuring out where the documentation and structure it neatly.
However in my opinion, the html documentation it generates does not look as good as it could, and unfortunately there is a limit to what you can do by changing the css, header and footer files. Luckily, doxygen has an option to export to XML.
What this project is aiming to do is to parse that xml data and generate some, hopefully better looking documentation and at the same time adding extendability to it so that users can change every detail of it if they want.

The project is written in python mainly because of its dynamic nature, making it easy to customize. Performance does not seem to be a very large problem so far during my testing.


## Ideas - Not Implemented Yet
- Related classes/pages. A plugin which searches the members of a class for 'see' tags and links in the descriptions and eventual code. It then creates a list of related items based on weighting of how many links there are to an item and where they were placed. This related items list could for example be placed in a sidebar for fast access.
