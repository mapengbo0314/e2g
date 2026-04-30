"""Prompts for Merger and Indexer Agents."""

from __future__ import annotations

import abc
from collections.abc import Sequence
import copy
import json
import textwrap
from typing import Final

import pydantic

from indexing import schema


# Local replacement for bundle_pb2.ProjectBundle.CustomSection
from dataclasses import dataclass as _dataclass


@_dataclass
class _CustomSection:
    """Stand-in for the upstream proto CustomSection."""
    title: str = ""
    prompt: str = ""


class _ProjectBundle:
    CustomSection = _CustomSection


class bundle_pb2:  # noqa: N801
    ProjectBundle = _ProjectBundle


MAX_CODE_SEARCH_QUERIES: Final[int] = 5
MAX_READ_FILE_QUERIES: Final[int] = 5

CODESEARCH_REFERENCE: Final[str] = textwrap.dedent("""\
Core Concepts

Regex Default: Queries are Regular Expressions (RE2 syntax) by default.
Unquoted text is treated as a regex.
foo. matches "food", "fool", etc.
Literal Search: Use double quotes "" for literal strings. Special characters
inside quotes are not interpreted.
"foo()" matches the literal "foo()".
Case Insensitive: Matching is case-insensitive by default (case:no).
Implicit AND: Space-separated terms are combined with AND.
foo bar finds files containing both "foo" AND "bar".
Negation: Use - to exclude terms.
foo -bar finds files containing "foo" but NOT "bar".
Escaping: Use \\ to escape special characters (e.g., \\, \\, (, )).
foo\\.bar matches "foo.bar" literally.
Word Boundaries: Use \\b for whole word matching.
\\bfoo\\b matches "foo" but not "foobar".
Logical Operators

AND: Logical conjunction (space is shorthand).
file:\\.py AND content:main
OR / |: Logical disjunction. | can be used within filter values.
lang:py OR lang:java
lang:py|java
( ): Grouping expressions. Note: Add spaces around parentheses, e.g.,
( foo OR bar ), to distinguish from regex grouping.
( content:foo OR content:bar ) AND lang:cc
Common Filters (Atoms)

content:<regex> / c:<regex>: Search within file contents.
c:MyClass
file:<regex> / f:<regex>: Search within file paths/names.
f:mono/my/project/.*\\.py$
-f:.*test\\.cc$ (Exclude test files)
lang:<lang> / l:<lang>: Filter by language (e.g., cc, java, py, go).
See go/cs-lang-reference.
l:py
symbol:<regex> / s:<regex>: Search for symbol definitions (classes,
functions, variables, etc.) as indexed by Kythe.
s:MyClass
s:my_namespace::MyFunction
class:<regex>: Search for class definitions,
class:MyClass
function:<regex> / func:<regex>: Search for function or method definitions,
func:HandleRequest
comment:<regex>: Search only within code comments,
comment:TODO
usage:<regex>: Search for matches not in comments or string literals,
usage:my_var
case:yes|no|auto: Set case sensitivity, auto is sensitive if the query has
uppercase letters. Default is no.
MyVar case:yes
within:<context> / w:<context>: Restrict content matches to lexical contexts
like string literal, comment. Can be negated with -.
c:"magic" within:stringliteral
c:TODO within:-comment
author:<user> / a:<user>: Files modified by a specific author in any
revision.
a:<USERNAME>
blame:<user>: Content sections where the last change was by <user>.
c:oops blame:<USERNAME>
at:<cl_number>: Search files at a specific CL snapshot,
f:myfile at_cl:123456789
from:<cl_number> / to:<cl_number>: Search within a CL range. to:0 means
HEAD.
from:0 includes all history.
c:new_feature from:123 to:456
removed:yes: Search only for code that has been deleted.
c:oldFunction removed:yes lang:java
repo:<repo> / r:<repo> & branch:<branch> / b:<branch>: Search in specific
Git-on-Borg repos.
contents:repo/google/foobar@master/main branch:main
git:repo/google/foobar@master branch:mainbranch
f:foo git:android/platform/superproject/main
project:<name>: Search across one or more UBlueprint projects.
(see go/cs-search-projects)
project:codesearch crs
protoid: Restrict to directories. -protoid for files only.
f:go id://project (truncated)
acl_workspace:<user/id or w:name>: Include results from a CitC workspace.
acl_workspace:<USERNAME>/1234
acl_workspace:eng
pcre:yes: Enables Perl Compatible Regular Expressions features.
pcre:yes (fns?func)\\(.*)
matcher:{regex|text|fuzzy} Specify matcher type. regex is default.
matcher:fuzzy f?jp?Ctrl
Regular Expressions (RE2 / PCRE)

Default engine is RE2 (go/re2syntax). Most regex matches are partial.
pcre:yes enables additional PCRE features like (?!), until-line,
(?s, dot all)...
""")

_KEY_G3_CONTEXT: Final[str] = textwrap.dedent("""\
Your prompt may encounter Google-internal concepts and jargon. Below are a few
facts about the codebase.

**1. Core Infrastructure & Concepts**

* **a. Distributed Computing & Resource Management**
  * **Borg / Borg cells:** Google’s system for managing and running large numbers of computer jobs across many machines. It acts as a giant scheduler.
  * **Borg cell:** A collection of machines, usually within a single datacenter, that are managed together by Borg. It represents a **neighborhood** or logical grouping of resources.
  * **Borg Prime:** The “brain” of a Borg cell. It's a server replicated for reliability that makes scheduling decisions.
  * **Borglet:** A program that runs on every machine in a Borg cell. It acts as a local agent, following the Borg Prime’s instructions to start, stop, and clean up jobs on the machine.
  * **Borg Job:** A description of a set of tasks that need to be run. A Borg policy defines the program, number of copies, and required resources.
  * **Borg Task:** A single running instance of a program within a Borg job. If a job specifies 100 copies, each copy is a task.
  * **Resource Containers:** A mechanism for isolating the resources (CPU, memory, disk) used by jobs, preventing tasks from interfering with each other.
  * **Borgcfg:** A command-line tool used to interact with Borg, allowing users to submit jobs, check status, and fetch logs.
  * **CellScore:** The system used by BorgProxy to determine the “best” Borg cell for a job, considering factors like resource availability and data locality.
  * **BorgCores:** A scheduler for CPU and memory within a cell, dealing with **allocation** and data location.
  * **Mars:** A system for scheduling and managing batch jobs on Borg, often used for non-latency-sensitive or infrequent jobs.
  * **Autopilot:** A resource allocation system built into Borg that automatically adjusts the resources allocated to running jobs based on real-time demand.
  * **Bns:** A system for naming services on Borg, providing a simplified and standardized way to deploy and operate them.
  * **Sigmar:** UI for viewing and managing Borg jobs.

* **2. Resource Units & Accounting**
  * **GU / Google Compute Unit:** Google’s internal unit for measuring computing power, providing a consistent way to compare the processing capability of different CPUs.
  * **Ganpati:** Google’s system for managing user accounts and groups within the production environment.
  * **FlexUs:** A system for managing the allocation of resources (CPU, memory, disk) to teams and projects within Borg and other infrastructure.
  * **Flex Limit:** The maximum amount of a specific resource (CPU, memory, disk) a team or project is allowed to use within a particular Borg cell.
  * **Resource Symphony:** A Borg resource allocation framework.
  * **Resource Optimization Tradeoffs (RoT):** A tool for calculating and comparing the cost of running a service under different resource configurations.
  * **PerfTune / Tune (Deprecated):** A deprecated dashboard that provided cost estimates for various resource-related settings.

* **3. Configuration Management**
  * **Borg Configuration Language (BCL):** A declarative language for writing Borg configuration files, describing how jobs should be run.
  * **BCL2:** An imperative language based on Python, also used for writing Borg configuration files.
  * **General Configuration Language (GCL):** A language Google uses to describe configurations.
  * **Pliny:** A system used to configure the Borg user for a server, connecting it with the appropriate product associations to determine resource access.
  * **Prodspec:** A system for modeling the desired state of production systems, used by P2020 Rollouts to determine necessary changes.
  * **Warpzone:** A way to represent a server’s footprint in your allocation model, in the deployed configuration.
  * **Prodplan:** Another way to represent a server’s footprint.

* **b. Networking**
  * **Jupiter:** Google’s modern, high-bandwidth, low-latency datacenter network fabric.
  * **Software-Defined Networking (SDN):** A network management approach where the control plane is separated from the data plane.
  * **B4:** Google’s SDN project for running Google’s global network and controlling inter-datacenter traffic.
  * **Global Traffic Controller (GTC):** The system that responds to DNS requests for Google services, directing users to the optimal datacenter.
  * **Google Front End (GFE):** Servers at the edge of Google’s network that receive internet traffic and perform tasks like SSL termination and request routing.
  * **Stubby:** A network front-end used by MetOps, SRE, PARMs, and service owners to view and manage the network.
  * **BorgProxy:** A service that allows access between Google’s corporate network (Corp) and production network (Prod).
  * **AutoBahn:** An encrypted transport service for accessing services in Google’s production network (Prod), typically requiring both machine and user credentials.
  * **CorpSSH:** A system allowing SSH access to desktops and servers, requiring Security Key authentication.
  * **Google Guest:** The wireless network provided for guests in Google offices.
  * **B2:** Google’s Backbone, a software-defined network. It connects core clusters and edge locations, handling high-priority, user-facing traffic.
  * **B4:** Google’s Beyond Backbone, a Software-Defined Network (SDN) connecting Google’s data centers.
  * **Peering routers:** Routers located at the edge of Google’s network that establish connections with other networks on the Internet.
  * **Caches:** Servers located at the edge of Google’s network that store copies of frequently accessed content.
  * **Metro PoPs:** A Point of Presence (PoP) located within a metropolitan area, providing network connectivity and services within that region.
  * **Edge PoP:** Likely a PoP at the edge of Google’s backbone network, providing high-capacity connections and routing between regions.
  * **Backbone PoP:** A PoP that is specifically part of the backbone network (B2 or B4), providing connectivity between different parts of the backbone.
  * **Network Service Level Objective (SLO):** A defined target for the performance and availability of network services.
  * **Quality of Service (QoS):** Mechanisms used to prioritize and manage different types of network traffic.

* **2. Load Balancing**
  * **Global Service Load Balancer (GSLB):** Google’s system for distributing traffic across multiple datacenters.
  * **Google Infrastructure Configuration Service (GICS):** Used for asking configuration changes to GSLB.
  * **application frontend (AFE):** The part of a service that handles requests from users or clients.
  * **application backend (ABE):** The part of a service that performs the actual processing and data storage.
  * **Viceroy:** A dashboard for viewing GSLB data and real-time traffic for a service. It replaced Forbin.
  * **Forbin (Deprecated):** The system replaced by Viceroy, which displayed GSLB data.

* **c. Storage**
  * **1. File Systems**
  * **Colossus:** Google’s distributed file system, a successor to GFS, designed for massive scale and high reliability.
  * **Chunks:** In the context of Colossus, these are the actual blocks of data that make up a file.
  * **Colossus File System (CFS):** The original version of Colossus, lacking true directory objects.
  * **Colossus namespace (CNS):** A layer built on top of CFS that provides real directory objects, making file management more hierarchical and user-friendly.
  * A `cns` path looks like `/cns/<cell-name>/home/<user-group>/...` while, for example, `/cns/d/<home>/ducile/path/to/file`.
  * **D servers:** Low-level storage servers providing the mapped access to the actual disks on which files are stored.
  * **CMETA:** Colossus Metadata, a Bigtable storing metadata about files in Colossus.
  * **Curator:** A component that handles file-level operations like creating, deleting, and storage server management.
  * **META:** NameSpace metadata, a table within CNS storing metadata about directories and files.
  * **Namespace compression:** Part of Colossus handling file-level or large operations, including directory operations, renames, and snapshots.
  * **Reed-Solomon:** An error-correcting code used by Colossus for redundancy.
  * **Nested encodings:** An extension of Reed-Solomon encoding used in Colossus.
  * **Google Drive:** Google’s cloud storage service for users, familiar to those outside of Google.
  * **x20:** An internal Google system for sharing large files and datasets, providing native file-level access from Linux desktops.
  * **Managed Storage:** A network storage solution (NPS or CIFS) for services in Google’s corporate datacenters.
  * **BinFS:** A system for securely distributing verified files from Google’s internal codebase (mono) to Googlers.

* **2. Databases**
  * **Bigtable:** A distributed, NoSQL database designed for handling massive amounts of structured data.
  * **Spanner:** A globally distributed, externally consistent database designed for strong consistency across multiple datacenters.
  * **F1:** A storage engine specifically designed for Spanner, improving performance and efficiency.
  * **SSTables:** “Sorted String Tables” - a persistent, ordered, immutable map from keys to values.

* **d. Accounts, Groups, and Authentication**
  * **Ganpati:** The secure system where your corporate account data is stored.
  * **Dasher user:** A user account within Google Workspace (formerly G Suite). This account is used for accessing Google’s public-facing services and is linked to the user’s google.com email address.
  * **CorpLogin (SSO):** The service that authenticates you to internal web applications and delegates credentials to other account systems.
  * **Gaia:** Google’s externally-available account service. It manages Google Accounts.
  * **Google Workspace:** The suite of online productivity tools (Gmail, Docs, Calendar, etc.) that Google uses internally and also sells to other companies.
  * **Active Directory (AD):** A directory service used by Windows.
  * **LDAP:** Lightweight Directory Access Protocol. At Google LDAP usage is mostly legacy.
  * **Bagpims:** Group System Comparison Documentation comparing the various group management systems.
  * **Google Groups:** The familiar Google Groups service.
  * **Gaia Groups:** A groups system used internally at Google.
  * **Low Overhead Authentication Service (LOAS):** A system for generating and managing short-lived credentials.
  * **SSH:** Secure Shell.
  * **gcert:** A command-line tool that generates temporary credentials (LOAS and SSH).

* **II. Software Development & Deployment**

* **a. Code Management & Version Control**
  * **mono:** Google’s massive, unified code repository.
  * **CodeSearch:** A web-based tool for browsing and searching code.
  * **Cider:** The Cloud IDE.
  * **monorepo:** Google’s internal version control system.
  * **Critique:** Google’s web-based tool for code review.
  * **Fugue:** A distributed version control system similar to Git.
  * **Git:** A widely used distributed version control system.
  * **Rebase:** A tool for managing multiple, dependent code changes in separate workspaces.

* **b. Build & Packaging**
  * **Blaze:** Google’s internal build system, used to compile code, run tests, and create packages.
  * **BUILD files:** Specify the software that can be built from code in a package, and the dependencies that exist between code.
  * **Forge:** A system that distributes and caches compilation jobs for Blaze.
  * **BuildRabbit:** Blaze in the cloud.
  * **Midas Package Manager (MPM):** A system for building, managing, and deploying packages of binary and static data files.

* **c. Testing**
  * **TAP (Test Automation Platform):** Google’s primary continuous build system.
  * **Guitar:** Google’s framework for larger-scale integration testing.
  * **AutoRollback:** A feature of TAP that automatically reverts code changes if they cause widespread test failures.
  * **Google Integration Testing Suite (ITS):** Provides tools for integration testing of servers and pipelines.
  * **SamMan (Deprecated):** A previously popular testing environment.
  * **Web Testing:** A framework within TAP for testing web applications by automating browsers.
  * **Hexa, hexabox, Mini, Scuba, Robolectric (Android), Earl Grey (iOS):** Various other testing tools.
  * **Sponge:** A centralized repository for the output of the build system (Blaze) and other test systems.
  * **Test Fusion:** The dashboard for Sponge V2.

* **d. Release Management & Deployment**
  * **Rapid (Release Automation Platform):** A service that automates the release process.
  * **Rollouts:** A suite of services for safely and consistently deploying code and configuration changes.
  * **P2020:** A set of tools and processes for modernizing Google’s production deployment and release management.
  * **Legislator:** A service within P2020 Rollouts that can run workflows.
  * **Annealing:** The part of P2020 Rollouts that actuates changes.
  * **Strategist:** A component of Annealing defining the strategy for how a rollout should proceed.
  * **Enforcer:** Another component of Annealing that enforces the rollout strategy.
  * **Prodspec:** A system for modeling the desired state of a production system.
  * **CAS (Canary Analysis Service):** Used to check if a recent change is causing problems.
  * **Rollouts UI:** The user interface for Rollouts.

* **e. IDEs and Editors**
  * **IntelliJ:** IntelliJ IDEA is a popular Java IDE.
  * **Cider V:** Cider V is Google’s next-generation IDE, based on VS Code.
  * **gLinux:** Google’s internal, managed distribution of Debian Linux.
  * **macOS:** The operating system used on Apple MacBooks.
  * **Chrome Remote Desktop (CRD):** A system allowing remote access to a Cloudtop instance.
  * **Cloudtop:** Google’s virtual desktop environment.
  * **VMware:** A virtualization platform.
  * **Puppet:** A configuration management system used to manage the configuration of all Linux, macOS, and Windows Corp machines.
  * **Rapture:** Google’s custom package repository and software deployment mechanism for Linux.
  * **GoogGet:** Google’s package management system for Windows.

* **III. Server-Side Technologies & Frameworks**

* **A. RPC & Communication**
  * **Stubby:** Google’s internal RPC framework.
  * **gRPC:** A high-performance, open-source RPC framework developed by Google.
  * **Protocol Buffers (Protobufs):** A method of serializing structured data.
  * **Borg Name Service (BNS):** A system mapping logical names like service names to the network addresses of the machines running that service.
  * **Chubby:** A distributed lock service.
  * **RPCs:** A system for defining who is allowed to access your server’s RPCs.
  * **BCID (Borg Caller ID):** A system that helps ensure that the binaries running in Borg were actually built from the correct source code in monorepo.
  * **Extensible Stubs:** The library that manages Stubby stubs.

* **B. Server Frameworks**
  * **Goa:** A framework for building servers in the Go programming language.
  * **AXI Web:** A framework for building specialized web applications.
  * **Scaffolding:** A framework for building servers in C++.
  * **Angular:** A popular framework for building web applications.
  * **Apps Framework:** A framework for building servers in Java or Kotlin.
  * **Boq Web:** A framework for building web applications, probably built on top of Boq.

* **C. Data Processing Pipelines**
  * **Flume:** Google’s internal framework for writing big data analysis pipelines.
    * **FlumeJava:** The Java API for Flume.
    * **FlumeC++:** The C++ API for Flume.
    * **FlumeGo:** The Go API for Flume.
    * **FlumePython:** The Python API for Flume.
    * **DAX:** A task management pipeline framework.
    * **Streaming Flume:** The streaming version of Flume.
  * **Apache Flume:** An unrelated open-source project.
  * **Apache Beam:** An open-source, unified programming model.
  * **PatchPanel (Deprecated):** A job launcher pipeline.
  * **Plx workflows:** Workflow utilities in the PLX ecosystem.
  * **DreamPipe:** Another potential replacement for PatchPanel.
  * **Workflow Task Master:** A system for managing work units (tasks).
  * **Analytics Task Manager:** A task management system.
  * **Placer:** A tool for copying input data files to a local processing datacenter.

* **IV. Monitoring, Alerting, & Incident Management**

* **A. Monitoring**
  * **Borgmon (Deprecated):** Google’s former primary monitoring system, now largely replaced by Monarch.
  * **Dumptruck (Deprecated):** Formerly used to store historical monitoring data from Borgmon.
  * **Prober Service:** Provides synthetic monitoring of services by sending real-world requests.
  * **Monarch:** Google’s current, global, high-performance monitoring system.
  * **Streamz:** An RPC service enabling Monarch to collect data from servers dynamically.
  * **Automon:** Automatically generates monitoring dashboards for every job in production.
  * **P2020 Monitoring Dashboards:** The new name for Automon.
  * **HTTP prober:** A built-in probe in Prober Service.
  * **Stubby prober:** A built-in probe in Prober Service.
  * **Common Execution Path (CEP) prober:** A more flexible way to define probes in Prober Service.
  * **Horizontal Monitoring Data (HMD):** HMD is a system for configuring dashboards, which monitor data is stored long-term in Monarch.
  * **Query Explorer (QE):** A tool for querying and visualizing the monitoring data stored in Monarch.
  * **gMon-Monarch alerting:** Libraries for defining custom alerts based on Monarch data.
  * **SLO Repository v2, and SLA Buckets:** Tools for defining and managing Service Level Objectives (SLOs) and Service Level Agreements (SLAs).
  * **vmprober:** A system for synthetic monitoring, likely focused on monitoring virtual machines (VMs).

* **B. Alerting & Notifications**
  * **Alert Manager:** Collects alerts from monitoring systems and sends notifications.
  * **AMC (Alert Manager Console) (Deprecated):** The user interface for Alert Manager.
  * **Customer User Journeys (CUJs) (Deprecated):** Formerly part of AMC, being replaced by features in IRM.
  * **Lifeguard:** A system for receiving pager alerts.
  * **SMS:** Short Message Service (text messaging), used for receiving pager alerts.
  * **Telebot:** Another system for receiving pager alerts.
  * **Escalator config:** Configuration for escalation paths.
  * **Mercury:** Documentation on escalation targets.
  * **Subspace:** A service where you configure how alert notifications are delivered.

* **C. Incident Management**
  * **IRM (Incident Response and Management):** The system for tracking outages and communicating their status.
  * **IMAG (Incident Management at Google):** The protocol used at Google for managing large-scale incidents.
  * **Tech-IR:** A team of senior SREs with expertise in running and resolving incidents.
  * **Delta SRE:** The team that developed the IMAG protocol.
  * **Incident Command System (ICS):** A standardized approach to incident management used by emergency response agencies.
  * **DRT (Disaster Recovery Testing):** Exercises to test Google’s ability to recover from major disasters.

* **D. Logging**
  * **Sawmill:** Google’s system for collecting, storing, and analyzing structured event logs.
    * **Envelope:** The Envelope is a process that runs alongside each server task and handles tasks like logging.
    * **Unified Logging Service (ULS):** ULS is the component of Sawmill that collects logs from server tasks.
    * **xulog / loge:** The two geo-replicated locations where Sawmill data is stored.
    * **Wipeout pipeline:** The pipeline that removes personally identifiable information (PII) from logs.
    * **Retention Team:** The team that manages retention and deletion policies for logs.
    * **Logs Proxy:** A service that enforces access control for logs in Sawmill.
  * **Eldar:** Eldar is part of the Sawmill system.
  * **Logs Front Door (LFD):** LFD is another web interface, also part of Sawmill.
  * **Remote Debug Logging (RDL):** RDL is the system that collects and stores the textual debug logs from your servers.
  * **AnaLog:** Analog is a web-based tool for searching and browsing through the textual debug logs.
  * **Dapper:** Dapper is Google’s distributed tracing system.

* **V. Troubleshooting & Debugging**

* **A. Tools & Systems**
  * **Debug handlers (aka z-pages):** Special web pages built into your server that show internal debugging information.
  * **Sherlog:** A system for tracing across-stack events.
  * **Third Eye:** A service that automatically reports on exceptions and errors logged by servers.
  * **Coroner:** A service that automatically collects and analyzes crash data for servers.
  * **Herodotus:** A service that keeps track of changes made to production systems.
  * **F1:** A service for performing SQL queries on logs data and other data sources.
    * **f1 Command-line tool:** The `f1-sql` command-line tool.
    * **f1 Query:** A system for querying and analyzing data from various sources.
    * **PLX:** A web UI for F1 and other query engines.
  * **Dremel (Deprecated):** A former system for interactive analysis of large datasets.
  * **PowerDrill (Deprecated):** A former tool for interactive data analysis, now replaced by PLX Explorer.
  * **Performance tools:** A general category of tools for analyzing server performance.
  * **pprof:** A widely-used tool for visualizing profiling information.
  * **rpcStudio:** A web-based tool for sending and receiving RPC requests.
  * **ServerThrottler:** A library that you can include in your server code to help it handle overload situations.
  * **YAQS (Yet Another Question System):** Google’s internal platform for asking and answering technical questions.

* **VI. Configuration & Experimentation**

* **A. Configuration Management**
  * **CDPush:** A system for pushing configuration data updates to servers without restarting them.
  * **Conductor:** Another system for pushing configuration data updates, similar to CDPush.

* **B. Experimentation**
  * **Mendel:** A system for managing experiments in production, allowing controlled rollout of changes to subsets of users or requests.
  * **Rasta:** A platform for analyzing A/B tests, comparing the performance of different versions of a feature.

* **VII. Guidelines**
Understand the difference between Google general guidelines and Google team specific guidelines (like GWS, Youtube, etc.).
* SQL refers to GoogleSQL.
* GoogleSQL is a standardized SQL dialect used in many query engines and services at Google, and is also released in open source as ZetaSQL.
  * GoogleSQL Query engines:
    * F1 Query
    * Dremel (now BigQuery)
    * Spanner
    * Cloud Spanner
    * Procella
    * Voxel (SQL evaluator library)
  * GoogleSQL Processing systems:
    * SQL Pipelines
    * Flume Relational Engine
    * PLX workflows
""")

OUTPUT_GOALS: Final[str] = textwrap.dedent("""\
Create overviews of a particular codebase with this output. Engineers and agents
use these summaries. They have access to the underlying codebase.
Write the summaries with the following goals:

## Content Goals

1. **Accuracy: CRITICAL GOAL** Ensure the summaries are free of errors.
Skip unknown information rather than providing incorrect information. Consumers
can reference the code to find missing information. Consumers may not realize
incorrect information in the summary is wrong. For example, do not guess acronym
meanings. Leave unresolved acronyms alone if you do not know the answer. Do not
expand acronyms unless the provided code context explicitly states the expansion.
2. **Completeness: CRITICAL GOAL** Include or point to all information
necessary to understand the code. Treat the summaries as a “map” of the codebase.
Do not explain every detail. Provide enough information to help a user quickly
find the right place to start reading code.
3. **Usefulness: CRITICAL GOAL** Make the summaries useful. Help a skilled
engineer understand the codebase. Ensure they know where to look for more detail
in as few steps as possible.
4. **Targeted Detail: Important Goal** Provide an appropriate level of detail
for each directory and component. Tune the level of detail based on complexity
and importance. Write very brief explanations of purpose for trivial files and
directories. A single sentence description suffices for simple utility classes.
Write detailed summaries for more complex files and directories. Explain the why
and how of the code in those summaries. For complex components, prioritize
explaining the core logic, key data structures, and interactions over listing
all public methods.

## Style Goals

1. **Objective Voice: CRITICAL GOAL** Write summaries in a neutral, objective
voice. Make them impersonal. Do not reflect the author’s point of view. Do not
waste words praising or criticizing the code. This wastes text.
2. **Code Excerpts: Important Goal** Do not include code excerpts within the
summaries. The consuming agent will have access to the codebase. It can get code
references itself. Direct code might confuse the agent. It might make the agent
think it has already inspected the codebase directly.
""")


def _output_format(schema_cls: type[pydantic.BaseModel]) -> str:
    """Returns the schema fields text for the indexer."""
    schema_str = json.dumps(schema_cls.model_json_schema(), indent=2)
    return textwrap.dedent("""\
CRITICAL:

Provide only a summary of the directory and its contents. Follow the
schema below exactly. Do not include any other information. Do not respond
multiple times. Do not ask clarifying questions.

{schema_str}

Avoid these common failure modes:
- Return a single object, not a list of objects.
- Do not include markdown formatting (like ```json ... ```) around the JSON.
- Do not add explanatory text before or after the JSON.
""").format(schema_str=schema_str)


class IndexerPrompt(abc.ABC):
    """Base class for the indexer prompts.

    Note that the indexer works in a sequential manner, first performing
    the code search, then reading the files, and then answering the final
    prompt.
    """

    def __init__(
        self,
        *,
        epoch: int,
        previous_epoch_str: str,
        directory_path: str,
        directory_contents: str,
        subdirectory_indexes: str,
        index_file_name: str,
        codebase_specific_context: str,
        custom_sections: Sequence[bundle_pb2.ProjectBundle.CustomSection],
        extra_context: str = "",
    ):
        self._epoch = epoch
        self._previous_epoch_str = previous_epoch_str
        self._directory_path = directory_path
        self._directory_contents = directory_contents
        self._subdirectory_indexes = subdirectory_indexes
        self._index_file_name = index_file_name
        self._codebase_specific_context = codebase_specific_context
        self._custom_sections = custom_sections
        self._extra_context = extra_context

    @abc.abstractmethod
    def role_description(self) -> str:
        raise NotImplementedError

    def prompt_context(self) -> str:
        return textwrap.dedent("""\
Summaries of immediate subdirectories from this epoch:
<SUBDIRECTORY_INDEXES>
{subdirectory_indexes}
</SUBDIRECTORY_INDEXES>

The index file name pattern for other directories is:
<INDEX_FILE_NAME>
{index_file_name}
</INDEX_FILE_NAME>
""").format(
            epoch=self._epoch,
            previous_epoch_str=self._previous_epoch_str,
            directory_path=self._directory_path,
            directory_contents=self._directory_contents,
            subdirectory_indexes=self._subdirectory_indexes,
            index_file_name=self._index_file_name,
        )

    def epoch(self) -> int:
        """Returns the epoch of the prompt."""
        return self._epoch

    def custom_sections(self) -> Sequence[bundle_pb2.ProjectBundle.CustomSection]:
        """Returns the custom sections of the prompt."""
        return self._custom_sections

    def codesearch_planner_instruction(self) -> str:
        """Returns the instruction for the codesearch planner agent."""
        agent_role = textwrap.dedent("""\
Your Role: You act as a researcher. You plan codebase searches to document a
directory's contents.
""")

        ability = textwrap.dedent("""\
Code search: You cannot perform code searches directly. You generate queries
for the code search tool. You can plan at most {max_code_search_queries} queries.
The system discards any extra queries. Use this language reference for the
codesearch query syntax:
<CODESEARCH_REFERENCE>
{codesearch_reference}
</CODESEARCH_REFERENCE>
""").format(
            codesearch_reference=CODESEARCH_REFERENCE,
            max_code_search_queries=MAX_CODE_SEARCH_QUERIES,
        )

        task = textwrap.dedent("""\
Your task:

1. Inspect the directory contents and any subdirectory summaries.
2. Create a research plan. Decide what information you need to gather via code
search to better understand the directory's code. Look at the files. Consider
important missing context pieces. Examples include consumed interface definitions,
exposed interface consumers, key production configurations, documentation, and tests.

IMPORTANT: format your output as a list of code search queries.
""")

        return textwrap.dedent("""\
{codebase_context}
{prompt_context}
{role_description}
{ability}
{task}""").format(
            role_description=agent_role,
            codebase_context=self._codebase_specific_context,
            ability=ability,
            prompt_context=self.prompt_context(),
            task=task,
        )

    def read_files_planner_instruction(
        self,
        *,
        code_search_output: str,
    ) -> str:
        """Returns the instruction for the read files planner agent."""
        agent_role = textwrap.dedent("""\
Your Role: You act as a researcher. You plan file reading to document a
directory's contents.
""")

        ability = textwrap.dedent("""\
Read files: You cannot read files directly. You generate a list of files for
the read files tool. You can plan to read at most {max_read_file_queries} files.
The system discards any extra files.
""").format(max_read_file_queries=MAX_READ_FILE_QUERIES)

        previous_context = textwrap.dedent("""\
Code search results:
<CODE_SEARCH_OUTPUT>
{code_search_output}
</CODE_SEARCH_OUTPUT>
""").format(
            code_search_output=code_search_output,
        )

        task = textwrap.dedent("""\
Your task:

Create a plan to read files to help summarize the directory.

1. Inspect the directory contents, subdirectory summaries, and code search
additional information.
2. Create a research plan. Decide what additional information you need to
gather by reading files. You already have access to all code in the directory.
Focus on reading other code within the codebase to better understand the directory's
code. Reading known files wastes time and lowers summary quality.

Use workspace-relative paths (e.g., 'foo/bar.py'). To locate files from imports,
be aware of the following language-specific quirks in mono:

* **C++:** Include paths are relative to `mono/`; you can use them verbatim.
  Example: `#include "foo/bar.h"` maps to `foo/bar.h`.
* **Java:** Imports generally map to paths relative to `mono/java/` or
  `mono/javatests/`. Example: `import com.google.foo.Bar;` maps to
  `recursive-index/foo/Bar.java`.
* **Python:** Absolute imports typically start with `mono.`. Example:
  `from mono.foo import bar` maps to `foo/bar.py`
* **Go:** Imports use the `mono/` prefix explicitly. Example:
  `import "mono/foo/bar"` maps to the package directory `foo/bar/`.

IMPORTANT: format your output as a list of files you want to read.
""")

        return textwrap.dedent("""\
{codebase_context}
{prompt_context}
{previous_context}
{role_description}
{ability}
{task}""").format(
            role_description=agent_role,
            codebase_context=self._codebase_specific_context,
            ability=ability,
            prompt_context=self.prompt_context(),
            previous_context=previous_context,
            task=task,
        )

    def custom_sections_instruction(
        self,
        *,
        code_search_output: str,
        read_files_output: str,
        key_components_output: str,
        deep_dive_output: str,
    ) -> str:
        """Returns the instruction for the custom sections agent.

        Args:
          code_search_output: The output from the initial code search.
          read_files_output: The output from reading the files.
          key_components_output: The summary of key components.
          deep_dive_output: The Deep dive summary.
        """
        previous_context = textwrap.dedent("""\
Code search results:
<CODE_SEARCH_OUTPUT>
{code_search_output}
</CODE_SEARCH_OUTPUT>

Read files results:
<READ_FILES_OUTPUT>
{read_files_output}
</READ_FILES_OUTPUT>

Key components summary:
<KEY_COMPONENTS_SUMMARY>
{key_components_output}
</KEY_COMPONENTS_SUMMARY>

Deep dive summary:
<DEEP_DIVE_SUMMARY>
{deep_dive_output}
</DEEP_DIVE_SUMMARY>
""").format(
            code_search_output=code_search_output,
            read_files_output=read_files_output,
            key_components_output=key_components_output,
            deep_dive_output=deep_dive_output,
        )

        agent_role = textwrap.dedent("""\
Your Role: You act as a technical writer on a team summarizing a large
codebase. You focus on synthesizing both general research and your
targeted specialized research to produce deep, domain-specific analysis
for the codebase.
""")

        task_instructions = [
            "Your task:",
            "",
            "1. Inspect the directory contents and any subdirectory summaries.",
            "2. Inspect the additional context from the previous research.",
            (
                "3. Generate the specific analysis sections requested by the user. "
                "For each section, generate a title and the full markdown content "
                "based on the provided instructions."
            ),
        ]

        if self._custom_sections:
            task_instructions.append(
                "4. You MUST generate the following requested sections based on the"
                " instructions:"
            )
        for section in self._custom_sections:
            task_instructions.append(
                f"*  - Title: {section.title}\n"
                f"      Instructions: {section.prompt}"
            )
        task = "\n".join(task_instructions)

        return textwrap.dedent("""\
{codebase_context}
{prompt_context}
{previous_context}
{role_description}
{output_goals}
{output_format}
{task}
""").format(
            role_description=agent_role,
            output_goals=OUTPUT_GOALS,
            output_format=_output_format(schema.CustomSectionsDocument),
            codebase_context=self._codebase_specific_context,
            task=task,
            prompt_context=self.prompt_context(),
            previous_context=previous_context,
        )

    def key_components_instruction(
        self,
        *,
        code_search_output: str,
        read_files_output: str,
    ) -> str:
        """Returns the instruction for the key components summary agent."""
        previous_context = textwrap.dedent("""\
Code search results:
<CODE_SEARCH_OUTPUT>
{code_search_output}
</CODE_SEARCH_OUTPUT>

Read files results:
<READ_FILES_OUTPUT>
{read_files_output}
</READ_FILES_OUTPUT>
""").format(
            code_search_output=code_search_output,
            read_files_output=read_files_output,
        )

        task = textwrap.dedent("""\
Your task:

1. Inspect the directory contents and any subdirectory summaries.
2. Inspect the additional context from the previous research.
3. Summarize the following sections for the directory: Key Components (Files and Subdirectories), Key Interfaces, Key Dependencies, and Configuration and Flags.
""")
        return textwrap.dedent("""\
{codebase_context}
{prompt_context}
{previous_context}
{role_description}
{output_goals}
{output_format}
{task}
{extra_context}
""").format(
            role_description=self.role_description(),
            codebase_context=self._codebase_specific_context,
            output_goals=OUTPUT_GOALS,
            prompt_context=self.prompt_context(),
            previous_context=previous_context,
            output_format=_output_format(schema.KeyComponentsDocument),
            task=task,
            extra_context=self._extra_context,
        )

    def deep_dive_instruction(
        self,
        *,
        code_search_output: str,
        read_files_output: str,
        key_components_output: str,
    ) -> str:
        """Returns the instruction for the deep dive summary agent."""
        previous_context = textwrap.dedent("""\
Code search results:
<CODE_SEARCH_OUTPUT>
{code_search_output}
</CODE_SEARCH_OUTPUT>

Read files results:
<READ_FILES_OUTPUT>
{read_files_output}
</READ_FILES_OUTPUT>

Key components summary:
<KEY_COMPONENTS_SUMMARY>
{key_components_output}
</KEY_COMPONENTS_SUMMARY>
""").format(
            code_search_output=code_search_output,
            read_files_output=read_files_output,
            key_components_output=key_components_output,
        )

        task = textwrap.dedent("""\
Your task:

1. Inspect the directory contents and any subdirectory summaries.
2. Inspect the additional context from the previous research.
3. Inspect the key components summary.
4. Write the Deep Dive section for the directory. Focus on the core logic, motivations, and technical details.

IMPORTANT: DO NOT repeat the information found in key components summary.
""")
        return textwrap.dedent("""\
{codebase_context}
{prompt_context}
{previous_context}
{role_description}
{output_goals}
{output_format}
{task}
{extra_context}
""").format(
            role_description=self.role_description(),
            codebase_context=self._codebase_specific_context,
            output_goals=OUTPUT_GOALS,
            output_format=_output_format(schema.DeepDiveDocument),
            prompt_context=self.prompt_context(),
            previous_context=previous_context,
            task=task,
            extra_context=self._extra_context,
        )

    def overview_instruction(
        self,
        *,
        code_search_output: str,
        read_files_output: str,
        key_components_output: str,
        deep_dive_output: str,
    ) -> str:
        """Returns the instruction for the final overview agent."""
        previous_context = textwrap.dedent("""\
Code search results:
<CODE_SEARCH_OUTPUT>
{code_search_output}
</CODE_SEARCH_OUTPUT>

Read files results:
<READ_FILES_OUTPUT>
{read_files_output}
</READ_FILES_OUTPUT>

Key components summary:
<KEY_COMPONENTS_SUMMARY>
{key_components_output}
</KEY_COMPONENTS_SUMMARY>

Deep dive summary:
<DEEP_DIVE_SUMMARY>
{deep_dive_output}
</DEEP_DIVE_SUMMARY>
""").format(
            code_search_output=code_search_output,
            read_files_output=read_files_output,
            key_components_output=key_components_output,
            deep_dive_output=deep_dive_output,
        )

        task = textwrap.dedent("""\
Your task:

1. Inspect the directory contents and any subdirectory summaries. Synthesize the
subdirectory information. Explain how subdirectories collectively contributes to
the current directory's overall purpose.
2. Inspect the additional context from the previous research, the key components summary, and the Deep Dive summary.
3. Provide the final response according to the output goals and format. Do not repeat the previous summaries. Focus
on synthesizing a higher-level overview.

IMPORTANT: keep the overview under 2 paragraphs (1000 words) and do not include any extra markdown formatting.
""")
        return textwrap.dedent("""\
{codebase_context}
{prompt_context}
{previous_context}
{role_description}
{output_goals}
{output_format}
{task}
{extra_context}
""").format(
            role_description=self.role_description(),
            codebase_context=self._codebase_specific_context,
            output_goals=OUTPUT_GOALS,
            output_format=_output_format(schema.OverviewDocument),
            prompt_context=self.prompt_context(),
            previous_context=previous_context,
            task=task,
            extra_context=self._extra_context,
        )


class InitialIndexerPrompt(IndexerPrompt):
    """Initial indexer prompt."""

    def role_description(self) -> str:
        del self  # Unused.
        return textwrap.dedent("""\
Your Role: You act as a technical writer on a team summarizing a large codebase.
Summarize the contents of a particular directory. Provide an overview of
its interactions with its subdirectories.
""")


class IndexImproverPrompt(IndexerPrompt):
    """Index improver prompt."""

    def role_description(self) -> str:
        del self  # Unused.
        return textwrap.dedent("""\
Your Role: You act as a technical writer on a team summarizing a large codebase.
Improve the summary of a particular directory. Improve the summary along one
of the dimensions from the output goals.

Cross-reference the 'existing_index' with the 'previous_root_map'. Identify
missing connections or contextual information.

Example improvements:

Make any improvements you see fit. Consider these impactful improvements:
- Correct inaccuracies. This provides the most impact. Fix any errors you spot.
- Add context about the directory's place in the larger project. Prior
iterations likely lacked this context.
- Improve tone, clarity, and flow.
- Improve usability. Engineers use the summary for context, background, and
navigating deeper information. Make the summary more scannable. Provide clearer
pointers to other interesting codebase areas.
- Make the summary concise without losing important information.
- Improve contextualization. The summary may inaccurately portray the directory's
role. It might claim this directory is the only solution, when others exist.
It might claim this directory solves a problem entirely, when it only provides
a partial solution.

Always improve! Look for opportunities to improve accuracy if you get stuck.
Find potentially wrong summary sections. Double check them against the code.
Identify and fix inaccuracies.
""")


def create_merger_prompt() -> str:
    return textwrap.dedent("""\
You act as a technical writer. Consolidate multiple partial directory summaries
into a single, coherent summary.

The system generated each partial summary from a subset of the files in the directory.
Merge them. Ensure the final output accurately reflects the combined content of all
partial summaries. Do not mention the partial summaries in the final summary.

{output_format}
""").format(output_format=_output_format(schema.IndexDocument))


def create_verifier_prompt(artifact_json: str, source_context: str) -> str:
    return textwrap.dedent(f"""\
You are an expert factual verifier for a codebase indexing system.
Your job is to read the generated artifact JSON and verify that EVERY claim made in it is explicitly supported by the source code context provided.

Rule 1: If the artifact claims a dependency, interface, or component exists, it MUST be visible in the source context.
Rule 2: If the artifact makes a claim about how something works, it MUST be supported by the code or comments in the source context.
Rule 3: You must NOT verify if the JSON structure is valid. Assume it is syntactically correct. Your job is ONLY semantic factual verification.
Rule 4: If you find ANY unsupported claims or hallucinated components/dependencies, you must mark `passed` as false and list the specific issues in the `issues` array.

=== SOURCE CONTEXT ===
{source_context}

=== GENERATED ARTIFACT ===
{artifact_json}

Return your verdict in the requested JSON format.
""")
