workspace {
    !identifiers hierarchical

    name "{{ product.name }}"

    model {
          properties {
            structurizr.groupSeparator "/"
            workspace_cmdb "{{ product.alias }}"
            architect "{{ architect_name }}"
          }

          my_system = softwareSystem mySystem {
            properties {
              "cmdb" "{{ product.alias }}"
            }
          }
    }

    views {
      properties { 
            plantuml.url "https://structurizr.vimpelcom.ru/plantuml"
            plantuml.format "svg"
            kroki.url "https://kroki.vimpelcom.ru/"
            kroki.format "svg"
            structurizr.sort created
            structurizr.tooltips true
        }
        
      theme https://structurizr.vimpelcom.ru/themes/beeline.json

      systemContext my_system {
        include *
        autoLayout
      }
    }
}