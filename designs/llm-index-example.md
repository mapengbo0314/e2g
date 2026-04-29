# Overview
The GMS Platform Onboarding directory contains a BoQ-based automation service designed to streamline the infrastructure setup for GMS Core modules and feature launches. This service provides a centralized RPC interface, defined in the proto subdirectory, that orchestrates complex workflows across multiple Google internal systems including Piper for version control, Rapid for release management, L-Space for artifact storage, and Gantry for project tracking and ACL management. By automating tasks such as mobilespec setup, feature flag configuration, and metric integration (e.g., Bottomline and Install Count), the service reduces the manual effort required from client teams during the module onboarding and rollout phases.
Architecturally, the directory is organized into specialized components that collaborate to provide this automation. The service subdirectory contains the core business logic implemented as BoO Actions, which leverage a suite of shared utilities in common for interacting with Piper, executing CodeMaker schematics for template-based code generation, and formatting files via fmtserver.
The client and keyregistryclient subdirectories provide the necessary communication layers for external consumers and internal dependencies, while server functions as the composite node for assembling the service into a deployable production unit. This structure facilitates a modular approach to infrastructure orchestration, supported by an asynchronous promisegraph framework that manages the dependencies between various infrastructure mutations.
# Deep Dive
The GMS Platform Onboarding directory implements a BoQ-based automation service designed to streamline the complex infrastructure requirements for GMS Core modules and feature launches. Instead of manual configuration across multiple disparate systems, this service provides a unified RC interface that orchestrates changes in code repositories, release management systems, and identity/access platforms.
### Core Orchestration Pattern
Most operations within this service follow a consistent asynchronous pattern managed via the BoQ promisegraph framework. A typical RPC workflow involves:
1. **Input Validation and Transformation**: Parameters from the proto request are often converted into standardized system identifiers using the Container' utility class, ensuring naming consistency across Piper, Rapid, and L-Space.
2. **Configuration Generation**: The service frequently uses CodemakerHelper' to invoke specific go/codemaker' schematics. These schematics utilize "textproto' templates to generate boilerplate configuration (e.g., BUILD files, GCL, or SCL definitions).
3. **Piper Automation**: The output from CodeMaker is passed to the 'PiperService", which automates the creation of a Cit workspace and a corresponding Piper changelist (CL). The service automatically adds reviewers, sets specific CL tags (like DO_NOT_SUBMIT or
"FLAG_NOT NEEDED'), and can trigger go/fitserver for file formatting before mailing the change

4. **Multi-System Provisioning**: For complex onboarding, the service parallelizes calls to other infrastructure APIs, such as provisioning BCID projects, setting up Gantry project ACLs (Ganpati groups and Zanzibar), or creating L-Space packages.
### Interactive Tool Automation
A unique aspect of this codebase is the SetupMobilespecAction, which automates the traditionally interactive mpplitool. It implements a stateful InteractiveMppcliSession' that launches the binary as a sub-process, monitors its stout for specific prompts (using rege), and provides the necessary responses via stdin to navigate the setup wizard. This is followed by a post-processing step (MobilespecC|Processor) that modifies the resulting Piper CL to ensure proper ownership and configuration.
### Infrastructure and Metrics Integration
The service also handles the
# Architectural Patterns and Gotchas
The codebase follows a modular BoQ architecture where RPC logic is encapsulated in Action classes within the service/ directory. A significant pattern is the orchestration of multiple external systems (Piper, Rapid, L-Space, Gantry) through "promisegraph. The Container' utility class is central for maintaining consistent naming conventions across these disparate systems (e.g., mapping a project name to its Mobilespec ID, Rapid releaser, and L-Space MDB groups). One notable implementation detail is the 'InteractiveMppliSession' in SetupMobilespecAction, which handles a stateful, interactive command-line session with mpcli by parsing its stout and providing inputs to stdin. Developers should be aware that many RPCs have long deadlines (up to 60 seconds) because they involve external mutations and CL creation.
# Key Individual Components
* service/: Contains the core implementation of the PlatformOnboardingService. It uses the BoQ Actions framework to handle various onboarding tasks such as setting up container APK definitions, provisioning Rapid runner resources, creating initial app listing CLs, and registering signing keys with L-Space. It includes dedicated service implementations for interacting with Rapid and Launch systems, and relies heavily on the common/' utilities for Piper and CodeMaker integration.
common/: A shared library providing essential utilities for the onboarding services. It includes 'PiperService for managing changelists in Piper, CodemakerHelper for executing go/codemaker schematics to generate code from templates, "FormatterHelper for invoking go/ftserver to format generated files, and "TechFileClientHelper' for interacting with the TechFile backend. It also provides common binding annotations and a stateful fake Piper service for testing.
* proto/: Defines the protocol buffer interfaces for the PlatformOnboardingService. This includes request and response messages for a wide array of automation tasks, such as
SetupMobilespec, CreateApplicationBcidPolicy, ProvisionRapidRunnerResources, and
'OnboardBottomlineMetrics
It uses the promise_bridge to facilitate integration with the BoQ
promisegraph framework.
* client/: The auto-generated BoQ client for the PlatformOnboardingService"
. It includes the
necessary modules and manifest configurations for other services to consume the onboarding RPCs.
*server/: The composite BoQ node that assembles the onboarding service for deployment. It contains the server configuration (server.pi") and GSLB settings for the production environment.
* keyregistryclient/: A specialized BoQ client for interacting with the Android Build Tools KeyRegistry service, used for retrieving signing key information during the onboarding process.
* 'AGENTS.md*: Governance and workflow documentation for Al agents operating within this directory, detailing the infrastructure stages of module stup, feature launch, and development rollout.
# Key Interfaces
gmsplatform.onboarding.proto.PlatformOnboardingService: The primary RCinterface for automating GMS Platform module onboarding. It provides methods for setting up Mobilespec IDs, Rapid blueprints, BCID policies, L-Space packages, and various metric integrations (Bottomline, Client Tracing, Install Count). Entry points are handled by specific Action classes in the servicel directory.
*com.google.gmsplatform.onboarding.common.PiperService': An abstraction layer for Piper operations, allowing the service to create changes from CodeMaker output, format CL files, mail changes for review, and manage CL tags programmatically
*com.google.gmsplatform.onboarding.service. RapidService: An internal service interface for interacting with Rapid, providing methods to fetch candidates by tag and trigger release creation workflows.
# Key Dependencies
- Apps Framework (BoQ): The foundational server framework providing the RPC dispatcher, authentication, and Action-based request handling.
- promisegraph: Used extensively for managing asynchronous logic and complex task orchestration across various infrastructure services.
- Piper API: Accessed via "PiperService" to automate the creation and management of Google3 changelists.
- CodeMaker: Used to generate boilerplate configuration and code files from textproto schematics.
- Rapid: Used for managing binary releases, candidates, and deployment workflows for GMS Platform containers.
-L-Space: Used for artifact storage and management, specifically for APKs and their associated signing keys.

- Ariane (Launch Service): Used to create and manage feature launch requests for new applications.
- Gantry Onboarding Service: Used to orchestrate Gantry project template generation and ACL setup (Ganpati groups and Zanzibar).
- KeyRegistry: Used to retrieve MD5 fingerprints and PEM certificates for application signing keys.
# Configuration and flags
* onboarding_dry_run
(java/com/google/gmsplatform/onboarding/common/BoqletModule.java): Global flag to enable dry run mode across onboarding RCs, preventing actual mutations in systems like Piper and L-Space. Comments: Default is false.
* codemaker_binary_path
(java/com/google/gmsplatform/onboarding/common/BoqletModule.java): Path to the CodeMaker binary used for template generation.
* mppli_binary_path"
(java/com/google/gmsplatform/onboarding/service/SetupMobilespecAction.java): Path to the mppc binary used for Mobilespec setup.
* rapid_url_hostname*
(java/com/google/gmsplatform/onboarding/service/CreatePlaceholderCandidateAction.java):
The hostname used to construct Rapid URLs in responses. Comments: Typically points to rapid.corp.google.com or rapid-qa.corp.google.com.
* Ispace
_instance (java/com/google/gmsplatform/onboarding/service/SpaceService.java):
Specifies the L-Space instance for artifact paths.
#Testing Strategy
Testing is primarily focused on unit tests for Action classes using RpcServiceTester' and the GoogleTestPromiseGraphModule'. These tests extensively use mocks (via Mockito') for external dependencies like "PiperService, "RapidService, and LSpaceService. A
"FakePiperService" is available in "common/testing for tests that require a stateful, predictable simulation of Piper operations. Integration tests for shell-based tools (like mppcli) utilize
"FakeExecutor and FakeProcess to simulate interactive tool behavior. Primary tests can be found in javatests/com/google/gmsplatform/onboarding/service/ (e.g.,
*SetupMobilespecActionTest.java', SetupContainerApkDefinitionsActionTest.java').
# All Subcomponents

* AGENTS.md
* BUILD
* client/BUILD
* client/BoqletModule.java
* client/README.md
* client/config/BUILD
* client/manifest/BUILD
* client/manifest/manifest.bzl
* common/BUILD
* common/BindingAnnotations.java
* common/BoqletModule.java
* common/CodemakerHelper.java
* common/CommandRunner.java
* common/FormatterHelper.java
* common/PiperService.java
* common/PiperServicelmpl.java
* common/README.md
* common/TechFileClientHelper.java
* common/config/BUILD
* common/manifest/BUILD
* common/manifest/manifest.bz
* common/testing/BUILD
* common/testing/FakePiperService.java
* keyregistryclient/BUILD
* keyregistryclient/BoqletModule.java
*keyregistryclient/config/BUILD
* keyregistryclient/manifest/BUILD
* keyregistryclient/manifest/manifest.bz
* proto/BUILD
* proto/platform_onboarding_service.proto
*server/BUILD
* server/README.md
*server/config/BUILD
*server/manifest/BUILD
* server/manifest/manifest.bzl
*service/BUILD
* service/BogletModule java
* service/Constants.java
* service/Container.java
*service/CreateApplicationBcidPolicyAction.java
* service/CreateGmsPlatformGantryProjectTemplateAction.java
* service/CreatelnitialAppListingCAction.java
* service/CreatelnitialAppListingLaunchAction.java
* service/CreateLspacePackageAction.java
* service/CreatePlaceholderCandidateAction.java
* service/EnableGabroConformanceTestSuitesAction.java
* service/GetMobilespecldStatusAction.java
* service/LSpaceService.java
* service/LaunchService.java

----- llm_index_V1.md
Preview
Source
1 # Overview
The GNS Platform Onboarding directory houses a Boo-based automation service that
simplifies the infrastructure lifecyete for GMS Core modules and feature launches. It serves as a cr
Architecturally, the directory 1s structured into modutar components: "service/
imptements the core business logié via BoQ Actions, white "common/" provides essential abstraction
# Deep Dive
The GNS Platform Onboarding service is a centralized automation hub designed to manage the lifecycle of GuS Core infrastructure, from initial module creation to feature rollout and
# Core Logic and Orchestration Pattern
service heavily utilizes the Bod "promisegraph' framework to manage the execution of multi-stage infrastructure mutations. Because these mutations often involve creating worksp
21
23
35
41
Infrastructure as Code via CodeMaker
dominant architectural pattern in this directory is the delegation of file generation to go/codemaker*, Instead of programmatically constructing complex files like BUILD, GCL, O one out eternal mplex componenes is the Setupblespecction". Uptike standard RPes that call other APTs, this actson automates the "pets" command-line tool. It t a Surgical Telemetry Onboarding
Several actions, such as OnboardBottomlineMetricsAction' and OnboardLientTradingLogCollectionAction', demonstrate a pattern of "surgical editing" of existing infrastructure file
# Security and Release Artifact Management
The service manages the secure transition of signing keys and BCID (Borg Caller ID) policies:
*BCID Policy: "CreateAppLicationBcidPoLicyAction'
ensures that applications have a defined security perimeter in production by creating projects and policies.
*Key Management**: The service interacts with the "KeyRegistry via a specialized client to retrieve MDS fingerprints and PEM certificates. These are used by "RegisterSigningke
**L-Space Provisioning: "CreateLspacePackageAction'automates the creation of artifact repositories and grants the necessary ALs for Rapid runners and team release operators.
Architectural Patterns and Gotchas
The codebase follows an orchestration agent pattern where BoQ Actions serve as high-level controllers that drive a sequence of external system mutations (Piper, Rapid, L-Space, Ga
* Key Individual Components
"proto/*: Defines the PlatformOnboardingService' RPC interface. It specifies a wide range of automation tasks for GMS Core infrastructure setup, includ
Mobilespec configurat
service/: Contains the core business logic of the onboarding service implemented as BoQ Actions. This directory orchestrates multi-step workflows across systems like Piper, Ra common/*: Provides shared utilities and abstraction layers used by the service actions. Key components include "PiperService' for managing changelists, "Codemakertetper' for ex client/: The auto-generated Boclient library for the PlatformOnboardingService'. It allows other services within Google to consume the onboarding automation RPCs by includ1
*server/': The composite Bod node configuration for deploying the onboarding service. It defines the server assembly (server-pi), including GSLsettings for routing traffic t
*keyregistryclient/: A dedicated BoQ client for the Android Build Tools KeyRegistry service. It is used during the onboarding process to retrieve signing key fingerprints and P AGENTS.nd': Governance and workflow documentation specifically for AI agents. It details the infrastructure stages (Module Setup, Feature Launch, Development & Rollout) and the
# Key Interfaces
*gmsplatform.onboarding.proto.PlatformOnboardingService': The primary RPC entry point for automating GMS Platform container and module onboarding. It provides high-level operati com.google.gmsplatform.onboarding.common.PiperService: An internal abstraction for Piper operations. It provides methods to create changelists from CodeMaker output, read/writ
*com.google.gmsplatform.onboarding.service.RapidService':Aninternal Interface for interacting with Rapid, providing methods to query recent candidates by tag and trigger the cl
* Key Dependencies
51
52
-Apps Framework (BoQ): The foundation for the service, providing the PC dispatcher, authentication, and Action-based request handling.
53
- promisegraph: Extensively used for orchestrating the complex, asynchronous dependencies between various infrastructure mutations.
54
- Piper API: Accessed via PiperService' to automate the creation and management of google3 changelists.
55
- CodeMaker: Invoked through Codemakertelper to generate boilerplate configuration files (BUILD, GCL, SCL, Proto) from textproto schematics.
- Rapid: Used to manage release blueprints, candidates, and deployment workflows for platform containers.
-L-Space: The repository for managing APK artifacts, ALs, and registering signing keys.
58
Gantry Onboarding Service: Orchestrated to provision project templates and manage access control via Ganpati and Zanzibar.
-Ariane (Launch Service): Used to programmatically create and manage feature launch requests.
- KeyRegistry: Provides signing key metadata and certificates for platform applications.
# Configuration and flags
62
64
65
66
67
68
onboarding_dry_run Java/com/google/gmsplatform/onboarding/common/BogletModule,javal: Global flag to enable dry run mode, preventing actual mutations in external systems 11ke Ps codemaker_binary_path (jaya/com/google/gmsplatform/onboarding/common/BoqletModule.java): Path to the 'codemaker binary used for schematic-based file generation. mppc1_binary_path (Jaya/com/google/gmsplatform/onboarding/service/SetupMobilespecAction.Java): Path to the mpect binary used for Mobilespec ID setup.
*
*rapid_urL_hostname(Java/com/google/gmsplatform/onbgarding/service/CreateRlaceholderCandidateAction.Java); The hostname used to construct Rapid URLs in response messages. Connen
*Ispace_Instance (Java/com/google/gmsplatform/onboarding/service/LSpaceservice.javal: Specifies the L-Space instance for artifact paths.
# Testing Strategy
Testing is centered on unit tests for Action classes Located in javatests/com/google/gl
73
# All Subcomponents
75 * AGENTS.nd
form/onboarding/service/'. These tests use RpcServiceTester
...
...