[![Tests](https://github.com/DataShades/ckanext-tour/actions/workflows/test.yml/badge.svg)](https://github.com/DataShades/ckanext-tour/actions/workflows/test.yml)

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
- Image (Optional): Visuals to complement the text, illustrate points, or add visual interest. GIF animation could be used here.

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
| 2.11 and below  | no            |
| 2.12+           | yes           |


## Installation

To install ckanext-tour:

1. Activate your CKAN virtual environment, for example:
    ```sh
    . /usr/lib/ckan/default/bin/activate
    ```
2. Clone the source and install it on the virtualenv
    ```sh
    git clone https://github.com/DataShades/ckanext-tour.git
    cd ckanext-tour
    pip install -e .
    ```
3. Add `tables files file_upload_widget tour` to the `ckan.plugins` setting in your CKAN
   config file (by default the config file is located at
   `/etc/ckan/default/ckan.ini`).

   The tour list is rendered with
   [ckanext-tables](https://github.com/DataShades/ckanext-tables), which is
   installed automatically as a dependency and must be enabled alongside `tour`.

   The `file_upload_widget` plugin is required for the file upload functionality.

4. Restart CKAN. For example if you've deployed CKAN with Apache on Ubuntu:

     `sudo service apache2 reload`

### Configuring File Storage

To store tour images, you need to configure file storage for the extension. Add the following settings to your `ckan.ini` file:

```ini
ckan.files.storage.tour_image.type = files:public_fs
ckan.files.storage.tour_image.path = %(ckan.storage_path)s/storage/tours
ckan.files.storage.tour_image.initialize = true
ckan.files.storage.tour_image.public_prefix = /tours
ckan.files.storage.tour_image.max_size = 10MiB
ckan.files.storage.tour_image.supported_types = image/png image/jpeg image/gif image/webp image/svg+xml
ckan.files.storage.tour_image.location_transformers = uuid4_with_extension

ckan.files.storage.tour_link.type = files:link
ckan.files.storage.tour_link.timeout = 5
```

## Config settings

```ini
# Start the tour automatically when the anchored page is loaded (default: false)
ckanext.tour.autoplay = false

# Default anchor element the tour attaches to (default: .breadcrumb .active)
ckanext.tour.default_anchor = .breadcrumb .active

# Collapse tour steps on the edit/create form (default: true)
ckanext.tour.collapse_steps = true
```

These options are runtime-editable and can also be changed from the tour
**Settings** page.

## Tests

To run the tests, do:
```sh
pytest --ckan-ini=test.ini
```

## License

[AGPL](https://www.gnu.org/licenses/agpl-3.0.en.html)
