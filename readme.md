# Documentation Post-Processor for Doxygen

Doxygen is a great documentation system. It is awesome at figuring out where the documentation and structure it neatly.
However in my opinion, the html documentation it generates does not look as good as it could, and unfortunately there is a limit to what you can do by changing the css, header and footer files. Luckily, doxygen has an option to export to XML.
What this project is aiming to do is to parse that xml data and generate some – hopefully better looking – documentation and at the same time making it more extandable so that users can change every detail of it if they want. In its current form it provides a much cleaner output than Doxygen and it also works reasonably well on mobile devices in contrast to Doxygen which does not work well at all there.

The project is written in python mainly because of its dynamic nature, making it easy to customize. The performance is decent, it can generate html output from doxygen's xml output in a few seconds for a medium sized project (≈40000 lines of code).

It has currently only been tested with source code C#.

Example output:
![example](/docs/example.png?raw=true "Example Output")

## Dependencies
- jinja2
- sass

## Installation
~~~~
# Install dependencies
pip3 install jinja2
sudo gem install sass

cd wherever/your/project/is
# Make sure Doxygen XML output is enabled
grep "GENERATE_XML" < Doxyfile
# GENERATE_XML           = YES
# Generate documentation (assume it goes into the xml directory)
./doxygen

git clone git@github.com:HalfVoxel/doxydoc.git
cd doxydoc
mkdir input
mv ../xml input
mkdir input/images
python3 doxydoc.py

# HTML has been generated in the 'html' directory
~~~~

## Ideas - Not Implemented Yet
- Related classes/pages. A plugin which searches the members of a class for 'see' tags and links in the descriptions and eventual code. It then creates a list of related items based on weighting of how many links there are to an item and where they were placed. This related items list could for example be placed in a sidebar for fast access.