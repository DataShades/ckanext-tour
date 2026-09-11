[![Tests](https://github.com/DataShades/ckanext-tour/actions/workflows/test.yml/badge.svg)](https://github.com/DataShades/ckanext-tour/actions/workflows/test.yml)

# ckanext-tour

ckanext-tour is a CKAN extension that provides a guided tour feature for CKAN instances. It allows users to create interactive tours to showcase different features and functionalities of a CKAN instance.

![ckanext-tour in action](https://raw.githubusercontent.com/DataShades/ckanext-tour/master/doc/example-1.png)

## Features
- Create interactive tours with step-by-step instructions
- Highlight specific elements on CKAN pages
- Customize tour appearance and behavior
- Easily manage and edit tours through the CKAN admin interface

Once the extension is installed and enabled, you can start creating tours through the CKAN admin interface. Each tour is bound to a page by its **Flask endpoint** (for example `dataset.read` covers every dataset page, or pick "Everywhere"), and you can define multiple steps for each tour.

Every page that has one or more tours shows a single floating **Start tour** button. If more than one tour applies, the button opens a short menu of their titles. A tour with **Start automatically** enabled also opens by itself the first time a visitor lands on a matching page; they can replay it from the button afterwards.

Each step contains next information:

- Title: A brief, engaging headline that summarizes the step.
- Query: CSS selector for the element we're highlighting
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
   `pip install -e .` also pulls in the three extensions `tour` depends on
   (see the table below).

3. Enable the plugins — add them to the `ckan.plugins` setting in your CKAN
   config file (by default `/etc/ckan/default/ckan.ini`):

   ```
   ckan.plugins = ... scheming_datasets tables files file_upload_widget tour
   ```

   | Package | Plugin(s) to enable | Needed for |
   | --- | --- | --- |
   | [ckanext-scheming](https://github.com/ckan/ckanext-scheming) | `scheming_datasets` (or any `scheming_*` plugin) | helpers used by the file_upload_widget |
   | [ckanext-tables](https://github.com/DataShades/ckanext-tables) | `tables` | rendering the tour list |
   | [ckanext-files](https://github.com/DataShades/ckanext-files) | `files`, `file_upload_widget` | storing and uploading step images |

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
ckan.files.storage.tour_link.protocols = https
```

## Config settings

See the available config options in [`config_declaration.yaml`](ckanext/tour/config_declaration.yaml).
Options marked `editable: true` there can also be changed from the tour **Settings** page.

## Tests

```sh
pip install -e '.[test]'
pytest --ckan-ini=test.ini
```

## License

[AGPL](https://www.gnu.org/licenses/agpl-3.0.en.html)
