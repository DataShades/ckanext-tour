[![Tests](https://github.com/DataShades/ckanext-tour/workflows/Tests/badge.svg?branch=main)](https://github.com/DataShades/ckanext-tour/actions)

# ckanext-tour

ckanext-tour is a CKAN extension that provides a guided tour feature for CKAN instances. It allows users to create interactive tours to showcase different features and functionalities of a CKAN instance.

## Features
- Create interactive tours with step-by-step instructions
- Highlight specific elements on CKAN pages
- Customize tour appearance and behavior
- Easily manage and edit tours through the CKAN admin interface

Once the extension is installed and enabled, you can start creating tours through the CKAN admin interface. Tours can be associated with specific pages or sections of your CKAN portal, and you can define multiple steps for each tour.

To start a tour, users can click on a tour trigger button or it can be started automatically, when user visits the specified page. The tour will guide them through the specified steps, highlighting the relevant elements on each page.

Each step contains next information:

- Title: A brief, engaging headline that summarizes the step.
- Query: Query to specify which element we're highlighting
- Intro: Text, that will be displayed on a step card
- Position: Specifies the placement of step card (top, right, bottom, left).
- Image: Visuals to complement the text, illustrate points, or add visual interest. GIF animation could be used here.

### Create Tour

To create a tour for ckanext-tour via the admin panel UI, follow these steps:

- Log in to your CKAN instance as a sysadmin.
- Navigate to the `Configuration` section in the admin panel toolbar.
- Find and click the `Add tour` link under the `Tour` section to open the tour creation form.
- Fill in the required information for the tour.
  - You can add 1 or more steps for each tour.
- Once you have added all the information, press `Create tour` button to submit the form and save the tour.
- Now you can go to the `List of tours` page and see all the tours that were created.


## Requirements

Compatibility with core CKAN versions:

| CKAN version    | Compatible?   |
| --------------- | ------------- |
| 2.9             | not tested    |
| 2.10+           | yes           |


## Installation

To install ckanext-tour:

1. Activate your CKAN virtual environment, for example:

     . /usr/lib/ckan/default/bin/activate

2. Clone the source and install it on the virtualenv

    git clone https://github.com/DataShades/ckanext-tour.git
    cd ckanext-tour
    pip install -e .
	pip install -r requirements.txt

3. Add `tour` to the `ckan.plugins` setting in your CKAN
   config file (by default the config file is located at
   `/etc/ckan/default/ckan.ini`).

4. Restart CKAN. For example if you've deployed CKAN with Apache on Ubuntu:

     sudo service apache2 reload


## Config settings

To modify the configuration of the extension, please make the changes through the site's user interface.

## Developer installation

To install `ckanext-tour` for development, activate your CKAN virtualenv and
do:

    git clone https://github.com/DataShades/ckanext-tour.git
    cd ckanext-tour
    python setup.py develop
    pip install -r dev-requirements.txt


## Tests

To run the tests, do:

    pytest --ckan-ini=test.ini


## License

[AGPL](https://www.gnu.org/licenses/agpl-3.0.en.html)
