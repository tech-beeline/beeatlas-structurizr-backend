workspace {
    name "BeeAtlas - Система управления архитектурой"
    description "Архитектура стенда системы BeeAtlas для демонстрации"
    
    !identifiers hierarchical
    
    model {
        properties {
            "workspace_cmdb" "fdmshowcaseapp"
        }
        
        // Персоны
        user = person "Пользователь" "Пользователь системы BeeAtlas"
        
        // Основная система
        BEEATLAS = softwareSystem "BeeAtlas" "Система управления архитектурой и цифровым описанием продуктов" {
            properties {
                "cmdb" "FDMSHOWCASEAPP"
            }
            
            // Группа фронтенда
            group "frontend" {
                container_ui = container "Web интерфейс" "Пользовательский интерфейс для работы с архитектурой" {
                    technology "React, TypeScript, JavaScript"
                    tags "frontend" "dev" "prod"
                    url https://beeatlas.ai-platform.pro/
                    
                    properties {
                        external_name frontend-arhitect-area
                    }
                }
            }
            
            // Группа API Gateway
            group "gateway" {
                container_api = container "API Gateway" "Единая точка входа для всех API запросов" {
                    technology "Spring, Java"
                    tags "gateway" "dev" "prod"
                    url https://api.beeatlas.ai-platform.pro/
                    
                    properties {
                        external_name fdm-gateway
                    }
                }
            }
            
            // Группа бэкенд сервисов
            group "backend" {
                container_product = container "Product Service" "Сервис управления продуктами" {
                    technology "Spring Boot, Java"
                    tags "backend" "dev" "prod"
                    
                    properties {
                        external_name fdm-products
                    }

                    component "Возможность получать информацию о архитектуре приложений" {
                        description "Возможность получать информацию о приложениях, интерфейсах и методах."
                        properties {
                            "type"          "capability"
                            "code"          "0002"
                            "parents"       "DMN.044"  
                        }
                    }

                    component "Получение данных об о всех приложениях" {
                            description "Получение данных обо всех приложениях — эта возможность архитектурного репозитория обеспечивает целостное представление о ландшафте программного обеспечения предприятия, выступая единым источником истины (Single Source of Truth) для всех заинтересованных сторон. Запрос к репозиторию возвращает агрегированный реестр приложений с их базовыми метаданными: уникальными идентификаторами, названиями, версиями, статусами жизненного цикла, назначенными владельцами и связями с бизнес-возможностями компании. Это позволяет архитекторам и ИТ-руководителям проводить инвентаризацию, выявлять дублирующиеся системы, оценивать технический долг на макроуровне и формировать стратегию развития архитектуры на основе актуальных и непротиворечивых данных со всего предприятия."
                            properties {
                                "type"          "capability"
                                "code"          "0003"
                                "parents"       "DMN.044"  
                            }
                        }
                    component "Получение данных об одном приложении" {
                            description "Получение данных об одном приложении — данная функция архитектурного репозитория предоставляет возможность глубокого погружения в детализированную карточку конкретной программной системы, раскрывая полный контекст ее существования в корпоративной среде. При запросе конкретного приложения репозиторий возвращает расширенный набор атрибутов, включающий его внутреннюю структуру (контейнеры и компоненты), используемый технологический стек, инфраструктурные зависимости (серверы, кластеры), связанные артефакты разработки (репозитории, пайплайны) и все входящие/исходящие интеграции с другими системами. Это позволяет архитекторам и разработчикам получить полное досье на систему для задач миграции, рефакторинга или аудита соответствия архитектурным стандартам без необходимости обращаться к разрозненным источникам информации."
                            properties {
                                "type"          "capability"
                                "code"          "0004"
                                "parents"       "DMN.044"  
                            }
                        }
                    component "Получение данных об интерфейсах и методах" {
                            description "Получение данных об интерфейсах и методах — эта возможность архитектурного репозитория обеспечивает видимость на уровне контрактов взаимодействия, фиксируя детальное поведение приложений и сервисов как часть управляемого архитектурного артефакта. Репозиторий хранит структурированные описания программных интерфейсов, включая протоколы доступа (REST, gRPC, асинхронные события), конкретные эндпоинты с их HTTP-методами, форматы запросов и ответов (JSON Schema, Avro), а также требования к аутентификации и авторизации. Это позволяет архитектурному репозиторию выступать в роли единого каталога API, гарантировать согласованность контрактов между командами, автоматизировать генерацию документации и обеспечивать соответствие реализации зафиксированным архитектурным решениям на самом детальном уровне."
                            properties {
                                "type"          "capability"
                                "code"          "0005"
                                "parents"       "DMN.044"  
                            }
                        }                            
                    
                    product_api = component "Product API" "API для управления продуктами" {
                        tags "api"
                        
                        properties {
                            type        api
                            protocol    rest
                            tc          0002
                            api_url     "https://api.beeatlas.ai-platform.pro/product"

                            "POST /api/v1/connection/interface" rps=20;latency=631;error_rate=2.90
                            "GET /api/v1/discovered-interface" rps=1;latency=901;error_rate=0.55
                            "PUT /api/v1/discovered-interface/{id}/operations" rps=9;latency=269;error_rate=2.49
                            "PUT /api/v1/discovered-interfaces" rps=7;latency=658;error_rate=1.84
                            "POST /api/v1/infra" rps=22;latency=765;error_rate=2.00
                            "GET /api/v1/mapic/product/{cmdb}/published-api" rps=23;latency=586;error_rate=0.72
                            "GET /api/v1/mapic/spec/{api-id}" rps=16;latency=196;error_rate=1.81
                            "GET /api/v1/product-tech-relation" rps=14;latency=575;error_rate=0.29
                            "POST /api/v1/product-tech-relation/{techId}" rps=15;latency=973;error_rate=2.06
                            "DELETE /api/v1/product-tech-relation/{techId}/{productId}" rps=25;latency=845;error_rate=2.42
                            "GET /api/v1/product/api-secret/{api-key}" rps=27;latency=816;error_rate=1.77
                            "GET /api/v1/product/by-ids" rps=25;latency=840;error_rate=1.41
                            "GET /api/v1/product/info" rps=4;latency=59;error_rate=0.55;tc=0003
                            "GET /api/v1/product/parent" rps=30;latency=632;error_rate=0.23
                            "GET /api/v1/product/{alias}/fitness-function" rps=11;latency=731;error_rate=1.58
                            "POST /api/v1/product/{alias}/fitness-function/{source_type}" rps=14;latency=572;error_rate=1.69
                            "GET /api/v1/product/{alias}/patterns" rps=11;latency=325;error_rate=2.50
                            "POST /api/v1/product/{alias}/patterns/{source-type}" rps=17;latency=855;error_rate=0.85
                            "GET /api/v1/product/{cmdb}/container" rps=30;latency=726;error_rate=1.87
                            "GET /api/v1/product/{cmdb}/e2e" rps=23;latency=205;error_rate=1.81
                            "GET /api/v1/product/{cmdb}/influence" rps=12;latency=276;error_rate=0.89
                            "GET /api/v1/product/{cmdb}/interface/arch" rps=1;latency=95;error_rate=1.61;tc=0005
                            "GET /api/v1/product/{cmdb}/interface/mapic" rps=26;latency=540;error_rate=2.28
                            "PATCH /api/v1/product/{cmdb}/source" rps=19;latency=645;error_rate=2.73
                            "GET /api/v1/product/{code}" rps=20;latency=698;error_rate=0.13
                            "PUT /api/v1/product/{code}" rps=11;latency=552;error_rate=0.60
                            "GET /api/v1/product/{code}/info" rps=19;latency=733;error_rate=2.06;tc=0004
                            "PUT /api/v1/product/{code}/relations" rps=3;latency=753;error_rate=2.25
                            "PATCH /api/v1/product/{code}/workspace" rps=10;latency=578;error_rate=2.80
                            "GET /api/v1/product/{id}/structurizr-key" rps=20;latency=494;error_rate=0.77
                            "GET /api/v1/product/{id}/tc-implementation" rps=19;latency=601;error_rate=0.72
                            "GET /api/v1/products/mnemonic" rps=8;latency=812;error_rate=2.92
                            "GET /api/v1/products/relations/tech" rps=25;latency=628;error_rate=1.74
                            "GET /api/v1/service/api-secret/{api-key}" rps=6;latency=684;error_rate=1.47
                            "GET /api/v1/tech/{techId}/product" rps=15;latency=450;error_rate=1.42
                            "GET /api/v1/user/product" rps=27;latency=951;error_rate=0.89
                            "GET /api/v1/user/product/admin" rps=10;latency=955;error_rate=1.96
                            "POST /api/v1/user/{id}/products" rps=30;latency=764;error_rate=0.37
                        }
                    }
                }
                
                container_cx_service = container "CX Service" "Сервис управления Customer Journey" {
                    technology "Spring Boot, Java"
                    tags "backend" "dev" "prod"
                    
                    properties {
                        external_name cx-backend
                    }
                    
                    cx_api = component "CX API" "API для управления Customer Journey и Business Interactions" {
                        tags "api"
                        
                        properties {
                            type        api
                            protocol    rest
                            api_url     "https://api.beeatlas.ai-platform.pro/cx"
                        }
                    }
                }
                
                container_user_service = container "User Service" "Сервис управления пользователями и авторизацией" {
                    technology "Spring Boot, Java"
                    tags "backend" "dev" "prod"
                    
                    properties {
                        external_name fdm-auth
                    }
                    
                    user_api = component "User API" "API для управления пользователями" {
                        tags "api"
                        
                        properties {
                            type        api
                            protocol    rest
                            api_url     "https://api.beeatlas.ai-platform.pro/auth"
                        }
                    }
                }
                
                container_techradar_service = container "Techradar Service" "Сервис управления технологическим радаром" {
                    technology "Spring Boot, Java 17"
                    tags "backend" "dev" "prod"
                    
                    properties {
                        external_name techradar-backend
                    }

                    component "Получение данных о технологиях по списку идентификаторов" {
                            description "Получение данных технологиях по списку идентификаторов — это возможность получения агрегированной информации о необходимых технологиях в рамках одного запроса"
                            properties {
                                "type"          "capability"
                                "code"          "0006"
                                "parents"       "DMN.044"  
                            }
                    }
                    
                    techradar_api = component "Techradar API" "API для управления технологиями" {
                        tags "api"
                        
                        properties {
                            type        api
                            protocol    rest
                            tc          0006
                            api_url     "https://api.beeatlas.ai-platform.pro/techradar"

                            "GET /api/v1/tech/by-ids" rps=1;latency=901;error_rate=0.55
                        }
                    }

                    
                            
                }
                
                container_capability_service = container "Capability Service" "Сервис управления бизнес-возможностями" {
                    technology "Spring Boot, Java 17"
                    tags "backend" "dev" "prod"
                    
                    properties {
                        external_name capability-backend
                    }

                    component "Получение данных о ТС по списку идентификаторов" {
                            description "Получение данных ТС по списку идентификаторов — это возможность получения агрегированной информации о необходимых ТС в рамках одного запроса"
                            properties {
                                "type"          "capability"
                                "code"          "0007"
                                "parents"       "DMN.044"  
                            }
                    }
                    
                    capability_api = component "Capability API" "API для управления бизнес-возможностями" {
                        tags "api"
                        
                        properties {
                            type        api
                            protocol    rest
                            tc          0007
                            api_url     "https://api.beeatlas.ai-platform.pro/capability"

                            "GET /api/v1/tech-capabilities/list/by-ids" rps=1;latency=901;error_rate=0.55
                        }
                    }
                }
                
                container_graph_service = container "Architect Graph Service" "Сервис работы с архитектурным графом" {
                    technology "Spring Boot, Java"
                    tags "backend" "dev" "prod"
                    
                    properties {
                        external_name architect-graph-service
                    }

                    component "Получение данных о deployment-node" {
                            description "Получение данных о deployment-node — это возможность получения информации о развертывании конкретного приложения"
                            properties {
                                "type"          "capability"
                                "code"          "0008"
                                "parents"       "DMN.044"  
                            }
                    }
                    
                    graph_api = component "Graph API" "API для работы с архитектурным графом" {
                        tags "api"
                        
                        properties {
                            type        api
                            protocol    rest
                            tc          0008
                            api_url     "https://api.beeatlas.ai-platform.pro/graph"

                            "GET /api/v1/search/deployment-node" rps=1;latency=901;error_rate=0.55
                        }
                    }
                }
                
                container_architect_graph_validator = container "Architect Graph Validator" "Сервис валидации архитектурного графа" {
                    technology "C++, Poco"
                    tags "backend" "dev" "prod"
                    
                    properties {
                        external_name architect-graph-validator
                    }
                    
                    validator_api = component "Validator API" "API для валидации архитектурного графа" {
                        tags "api"
                        
                        properties {
                            type        api
                            protocol    rest
                            api_url     "https://api.beeatlas.ai-platform.pro/validator"
                        }
                    }
                }
                
                container_architecture_center_template = container "Architecture Center Template" "Сервис шаблонов архитектурного центра" {
                    technology "Spring Boot, Java, Python"
                    tags "backend" "dev" "prod"
                    
                    properties {
                        external_name architecture-center-template-backend
                    }
                }
                
                container_ambassador = container "Ambassador" "Сервис интеграции с внешними системами" {
                    technology "Spring Boot, Java"
                    tags "backend" "dev" "prod"
                    
                    properties {
                        external_name ambassador
                    }
                }
                
                container_event_service = container "Event Service" "Сервис истории событий" {
                    technology "Spring Boot, Java"
                    tags "backend" "dev" "prod"
                    
                    properties {
                        external_name events-history
                    }
                }
                
                container_doc_service = container "Document Service" "Сервис управления документами" {
                    technology "Spring Boot, Java"
                    tags "backend" "dev" "prod"
                    
                    properties {
                        external_name document-service
                    }
                }
                
                container_camunda_service = container "Camunda Service" "Сервис управления бизнес-процессами" {
                    technology "Spring Boot, Java 17, Camunda"
                    tags "backend" "dev" "prod"
                    
                    properties {
                        external_name fdm-bpm
                    }
                }
                
                pack_loader_service = container "Pack Loader Service" "Сервис загрузки пакетов данных" {
                    technology "Spring Boot, Java 17"
                    tags "backend" "dev" "prod"
                    
                    properties {
                        external_name fdm-pack-loader
                    }
                    
                    pack_load_api = component "Pack Load API" "API для загрузки пакетов" {
                        tags "api"
                        
                        properties {
                            type        api
                            protocol    rest
                            api_url     "https://api.beeatlas.ai-platform.pro/pack-loader"
                        }
                    }
                }
                
                notify_service = container "Notify Service" "Сервис управления уведомлениями" {
                    technology "Spring Boot, Java 17"
                    tags "backend" "dev" "prod"
                    
                    properties {
                        external_name fdm-notifications-management
                    }
                    
                    notify_api = component "Notify API" "API для управления уведомлениями" {
                        tags "api"
                        
                        properties {
                            type        api
                            protocol    rest
                            api_url     "https://api.beeatlas.ai-platform.pro/notify"
                        }
                    }
                }
                
                structurizr_backend = container "Structurizr Backend" "Сервис управления рабочими пространствами Structurizr" {
                    technology "Python"
                    tags "backend" "dev" "prod"
                    
                    properties {
                        external_name structurizr_backend
                    }
                    
                    structurizr_api = component "Structurizr API" "API для управления Structurizr workspace" {
                        tags "api"
                        
                        properties {
                            type        api
                            protocol    rest
                            api_url     "https://api.beeatlas.ai-platform.pro/structurizr"
                        }
                    }
                }
            }
            
            // Группа хранилищ данных
            group "storage" {
                container_database = container "База данных" "Основное хранилище данных системы" {
                    technology "PostgreSQL 14"
                    tags "database" "dev" "prod"
                }
                
                container_message_queue = container "Очередь сообщений" "Очередь для асинхронной обработки событий" {
                    technology "RabbitMQ"
                    tags "queue" "dev" "prod"
                }
                
                container_file_storage = container "Файловое хранилище" "Хранилище документов и файлов" {
                    technology "MinIO (S3)"
                    tags "storage" "dev" "prod"
                }
                
                neo4j = container "Neo4j" "Графовая база данных для архитектурного графа" {
                    technology "Neo4j"
                    tags "database" "dev" "prod"
                }
                
                redis = container "Redis" "Кэш для повышения производительности" {
                    technology "Redis"
                    tags "cache" "dev" "prod"
                }
            }
            
            // Группа Structurizr
            group "structurizr" {
                structurizr = container "Structurizr On-Premises" "Сервер Structurizr для визуализации архитектуры" {
                    technology "Java, Tomcat"
                    tags "structurizr" "dev" "prod"
                    url https://structurizr.ai-platform.pro/
                }
            }
        }
        
        // Внешние системы
        AUTHENTIK = softwareSystem "Authentik" "Система аутентификации и авторизации" {
            tags "external"
            url https://auth.ai-platform.pro/
            properties {
                "cmdb" "Authentik"
            }
        }
        
        // Связи между элементами
        BEEATLAS.container_product.product_api -> BEEATLAS.container_techradar_service.techradar_api "Запрос технологий приложений" "HTTPS:443"
        BEEATLAS.container_product.product_api -> BEEATLAS.container_capability_service.capability_api "Запрос ТС приложений" "HTTPS:443"
        BEEATLAS.container_product.product_api -> BEEATLAS.container_graph_service.graph_api "Получение deployment-node приложений"
        
        // Связи пользователей с системой
        user -> BEEATLAS.container_ui "Использует интерфейс" "HTTPS:443"
        
        // Связи UI с API Gateway
        BEEATLAS.container_ui -> BEEATLAS.container_api "Вызывает API" "HTTPS:443"
        BEEATLAS.container_ui -> AUTHENTIK "Аутентификация" "HTTPS:443"
        
        // Связи API Gateway с сервисами
        BEEATLAS.container_api -> BEEATLAS.container_product.product_api "Маршрутизация запросов" "HTTPS:443"
        BEEATLAS.container_api -> BEEATLAS.container_cx_service.cx_api "Маршрутизация запросов" "HTTPS:443"
        BEEATLAS.container_api -> BEEATLAS.container_user_service.user_api "Маршрутизация запросов" "HTTPS:443"
        BEEATLAS.container_api -> BEEATLAS.container_techradar_service.techradar_api "Маршрутизация запросов" "HTTPS:443"
        BEEATLAS.container_api -> BEEATLAS.container_capability_service.capability_api "Маршрутизация запросов" "HTTPS:443"
        BEEATLAS.container_api -> BEEATLAS.container_graph_service.graph_api "Маршрутизация запросов" "HTTPS:443"
        BEEATLAS.container_api -> BEEATLAS.container_architect_graph_validator.validator_api "Маршрутизация запросов" "HTTPS:443"
        BEEATLAS.container_api -> BEEATLAS.structurizr_backend.structurizr_api "Маршрутизация запросов" "HTTPS:443"
        
        // Связи сервисов с базой данных
        BEEATLAS.container_product -> BEEATLAS.container_database "Хранит данные продуктов" "TCP:5432"
        BEEATLAS.container_cx_service -> BEEATLAS.container_database "Хранит данные CJ/BI" "TCP:5432"
        BEEATLAS.container_user_service -> BEEATLAS.container_database "Хранит данные пользователей" "TCP:5432"
        BEEATLAS.container_techradar_service -> BEEATLAS.container_database "Хранит данные технологий" "TCP:5432"
        BEEATLAS.container_capability_service -> BEEATLAS.container_database "Хранит данные возможностей" "TCP:5432"
        BEEATLAS.container_doc_service -> BEEATLAS.container_database "Хранит метаданные документов" "TCP:5432"
        BEEATLAS.pack_loader_service -> BEEATLAS.container_database "Хранит данные пакетов" "TCP:5432"
        BEEATLAS.notify_service -> BEEATLAS.container_database "Хранит данные уведомлений" "TCP:5432"
        BEEATLAS.container_event_service -> BEEATLAS.container_database "Хранит историю событий" "TCP:5432"
        
        // Связи с очередью сообщений
        BEEATLAS.container_product -> BEEATLAS.container_message_queue "Публикует события" "AMQP:5672"
        BEEATLAS.container_capability_service -> BEEATLAS.container_message_queue "Публикует события" "AMQP:5672"
        BEEATLAS.container_techradar_service -> BEEATLAS.container_message_queue "Публикует события" "AMQP:5672"
        BEEATLAS.container_event_service -> BEEATLAS.container_message_queue "Публикует события" "AMQP:5672"
        BEEATLAS.pack_loader_service -> BEEATLAS.container_message_queue "Подписывается на события" "AMQP:5672"
        BEEATLAS.notify_service -> BEEATLAS.container_message_queue "Подписывается на события" "AMQP:5672"
        
        // Связи с файловым хранилищем
        BEEATLAS.container_doc_service -> BEEATLAS.container_file_storage "Сохраняет документы" "HTTPS:443"
        BEEATLAS.structurizr_backend -> BEEATLAS.container_file_storage "Сохраняет workspace" "HTTPS:443"
        
        // Связи с Neo4j
        BEEATLAS.container_graph_service -> BEEATLAS.neo4j "Запись/чтение архитектурного графа" "Bolt:7687"
        
        // Связи с Redis
        BEEATLAS.container_graph_service -> BEEATLAS.redis "Кэширование задач" "TCP:6379"
        
        // Связи с Structurizr
        BEEATLAS.structurizr_backend -> BEEATLAS.structurizr "Создание workspace, загрузка данных" "HTTPS:443"
        
        // Deployment Environment
        deploymentEnvironment "SIBUR-STEND" {
            deploymentNode "VM-1" {
                properties {
                    "ip" "10.204.205.167"
                }
                
                deploymentNode "docker-vm1" {
                    properties {
                        "type" "docker"
                    }
                    
                    deploymentNode "apps_neo4j" {
                        containerInstance BEEATLAS.neo4j
                        properties {
                            ip 10.0.0.1
                            flavor cpu4ram8
                        }
                    }
                    
                    deploymentNode "apps_structurizr" {
                        containerInstance BEEATLAS.structurizr
                        properties {
                            ip 2001:4860:4860::8888
                            flavor cpu4ram16
                        }
                    }
                    
                    deploymentNode "apps_rabbitmq" {
                        containerInstance BEEATLAS.container_message_queue
                        properties {
                            flavor cpu2ram4
                            volume_size 50
                        }
                    }
                    
                    deploymentNode "apps_minio" {
                        containerInstance BEEATLAS.container_file_storage
                        properties {
                            ip 192.168.1.1
                            flavor cpu2ram4
                            volume_size 20
                        }
                    }
                    
                    deploymentNode "apps_postgres" {
                        containerInstance BEEATLAS.container_database
                        properties {
                            ip 122.133.144.155
                            flavor 4cpu32ram
                            volume_size 50
                        }
                    }
                    
                    deploymentNode "apps_redis" {
                        containerInstance BEEATLAS.redis
                        properties {
                            ip 8.8.8.8
                            flavor cpu1ram1
                        }
                    }
                }
            }
            
            deploymentNode "VM-2" {
                properties {
                    "ip" "10.204.205.9"
                }
                
                deploymentNode "docker-vm2" {
                    properties {
                        "type" "docker"
                    }
                    
                    deploymentNode "apps_frontend-arhitect-area" {
                        containerInstance BEEATLAS.container_ui
                        properties {
                            host ui.ai.ru
                            flavor cpu1ram2
                        }
                    }
                    
                    deploymentNode "apps_fdm-gateway" {
                        containerInstance BEEATLAS.container_api
                        properties {
                            external_ip 8.8.8.8
                            flavor cpu1ram2
                        }
                    }
                    
                    deploymentNode "apps_architecture-center-template-backend" {
                        containerInstance BEEATLAS.container_architecture_center_template
                        properties {
                            flavor cpu1ram2
                        }
                    }
                    
                    deploymentNode "apps_architect-graph-validator" {
                        containerInstance BEEATLAS.container_architect_graph_validator
                        properties {
                            flavor cpu1ram2
                        }
                    }
                    
                    deploymentNode "apps_fdm-products" {
                        containerInstance BEEATLAS.container_product
                        properties {
                            flavor cpu1ram2
                        }
                    }
                    
                    deploymentNode "apps_structurizr-backend" {
                        containerInstance BEEATLAS.structurizr_backend
                        properties {
                            flavor cpu1ram2
                        }
                    }
                    
                    deploymentNode "apps_cx-backend" {
                        containerInstance BEEATLAS.container_cx_service
                        properties {
                            flavor cpu1ram2
                        }
                    }
                    
                    deploymentNode "apps_fdm-auth" {
                        containerInstance BEEATLAS.container_user_service
                        properties {
                            flavor cpu1ram2
                        }
                    }
                    
                    deploymentNode "apps_techradar-backend" {
                        containerInstance BEEATLAS.container_techradar_service
                        properties {
                            flavor cpu1ram2
                        }
                    }
                    
                    deploymentNode "apps_authentik" {
                        softwareSystemInstance AUTHENTIK
                        properties {
                            flavor cpu2ram4
                        }
                    }
                    
                    deploymentNode "apps_capability-backend" {
                        containerInstance BEEATLAS.container_capability_service
                        properties {
                            flavor cpu1ram2
                        }
                    }
                    
                    deploymentNode "apps_fdm-bpm" {
                        containerInstance BEEATLAS.container_camunda_service
                        properties {
                            flavor cpu1ram2
                        }
                    }
                    
                    deploymentNode "apps_fdm-pack-loader" {
                        containerInstance BEEATLAS.pack_loader_service
                        properties {
                            flavor cpu1ram2
                        }
                    }
                    
                    deploymentNode "apps_fdm-notifications-management" {
                        containerInstance BEEATLAS.notify_service
                        properties {
                            flavor cpu1ram1
                        }
                    }
                    
                    deploymentNode "apps_ambassador" {
                        containerInstance BEEATLAS.container_ambassador
                        properties {
                            flavor cpu1ram2
                        }
                    }
                    
                    deploymentNode "apps_events-history" {
                        containerInstance BEEATLAS.container_event_service
                        properties {
                            flavor cpu1ram2
                        }
                    }
                    
                    deploymentNode "apps_document-service" {
                        containerInstance BEEATLAS.container_doc_service
                        properties {
                            flavor cpu1ram2
                        }
                    }
                    
                    deploymentNode "apps_arch-graph-service" {
                        containerInstance BEEATLAS.container_graph_service
                        properties {
                            flavor cpu1ram2
                        }
                    }
                }
            }
        }
    }
    
    views {
        systemContext BEEATLAS {
            include *
            autoLayout
        }
        
        container BEEATLAS "containers-main" "Диаграмма контейнеров системы BeeAtlas" {
            include *
            #exclude element.tag==external
            autoLayout lr
        }
        
        
        // Deployment View
        deployment BEEATLAS "SIBUR-STEND" "deployment-stend" "Диаграмма развертывания на стенде SIBUR" {
            title "Диаграмма развёртывания системы BeeAtlas на стенде SIBUR"
            include *
            autoLayout lr
        }

        dynamic BEEATLAS.container_product "0003" "Получение информации по всем приложениям" {
            autoLayout lr
            title "Получение информации по всем приложениям"
            BEEATLAS.container_api -> BEEATLAS.container_product.product_api "GET /api/v1/product/info"
            BEEATLAS.container_product.product_api -> BEEATLAS.container_techradar_service.techradar_api "GET /api/v1/tech/by-ids"
            BEEATLAS.container_product.product_api -> BEEATLAS.container_capability_service.capability_api "GET /api/v1/tech/by-ids"
        }

        dynamic BEEATLAS.container_product "0004" "Получение информации по одному приложению" {
            autoLayout lr
            title "Получение информации по одному приложению"
            BEEATLAS.container_api -> BEEATLAS.container_product.product_api "GET /api/v1/product/{code}/info"
            BEEATLAS.container_product.product_api -> BEEATLAS.container_techradar_service.techradar_api "GET /api/v1/tech/by-ids"
            BEEATLAS.container_product.product_api -> BEEATLAS.container_capability_service.capability_api "GET /api/v1/tech/by-ids"
        }

        dynamic BEEATLAS.container_product "0005" "Получение информации о интерфейсах приложения" {
            autoLayout lr
            title "Получение информации о интерфейсах приложения"
            BEEATLAS.container_api -> BEEATLAS.container_product.product_api "GET /api/v1/product/{cmdb}/interface/arch"
            BEEATLAS.container_product.product_api -> BEEATLAS.container_capability_service.capability_api "GET /api/v1/tech/by-ids"
        }
        
        // Настройки views
        properties {
            structurizr.sort created
            structurizr.tooltips true
        }
        
        // Стили элементов
        styles {
            element "Person" {
                shape Person
                background #08427b
                color #ffffff
            }
            
            element "Software System" {
                background #1168bd
                color #ffffff
            }
            
            element "Container" {
                background #438dd5
                color #ffffff
            }
            
            element "Component" {
                background #85bbf0
                color #000000
            }
            
            element "DeploymentNode" {
                background #999999
                color #ffffff
            }
            
            element "tag:external" {
                background #999999
                color #ffffff
                opacity 50
            }
            
            element "frontend" {
                background #ff6b6b
                color #ffffff
            }
            
            element "backend" {
                background #4ecdc4
                color #ffffff
            }
            
            element "gateway" {
                background #95e1d3
                color #000000
            }
            
            element "database" {
                shape Cylinder
                background #438dd5
                color #ffffff
            }
            
            element "queue" {
                shape Pipe
                background #f38181
                color #ffffff
            }
            
            element "storage" {
                background #a8e6cf
                color #000000
            }
            
            element "cache" {
                background #ffd93d
                color #000000
            }
            
            element "api" {
                background #ffd93d
                color #000000
            }
            
            element "structurizr" {
                background #6bcf7f
                color #000000
            }
            
            relationship "Relationship" {
                routing Direct
                thickness 2
            }
        }
    }
}
