# Export as Fixture

Export selected queryset as fixtures using any registered Serializer.

!!! note annotate

    this is not the same as django's command ``dumpdata`` because it can dump also the Foreign Keys.


|||
|--------------------|---------------------------------------------------------------------------------------|
**use natural key**  | If true use natural keys.
**dump on screen**   | Dump on screen instead to show ``Save as`` popup
**indent**           | Indentation value
**serializer**       | Serializer to use. (see :ref:`Serialization formats <django:serialization-formats>`)
**add_foreign_keys** | If checked export foreign keys too, otherwise act as standard dumpdata


**Screenshot**

![export_as_fixture](_static/export_as_fixture.png)
