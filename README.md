# Agentic UI Mapper

Agentic UI Mapper is a Windows desktop UI exploration and representation tool. It observes a running desktop application, detects visible controls and text from screenshots, groups related elements, and builds a persistent **functional DOM (fDOM)**.

The result is a machine-readable map of an application's screens, UI elements, and transitions. Unlike a browser DOM, an fDOM is created from visual evidence and interaction outcomes, so it can describe native Windows applications that do not expose an HTML document.

## What the project does

The project combines computer vision, OCR, optional multimodal analysis, and controlled desktop interaction to answer questions such as:

- What controls are visible in this application state?
- Where is each control located?
- What does an element appear to represent?
- Is an element enabled or interactive?
- Which new state appears after clicking it?
- How can the application be navigated back to a previously observed state?

The main persistent artifact is `fdom.json`. It contains states, detected nodes, metadata, and edges between states. Supporting screenshots, crops, templates, visual differences, and analysis files are stored under the corresponding application folder in `apps/`.

## Important terminology

| Term | Meaning |
| --- | --- |
| fDOM | Functional DOM: a visual and behavioral map of a desktop application's UI. |
| State | A distinct application screen or visual configuration, beginning with `root`. |
| Node | A detected UI element such as an icon, button, menu item, or text region. |
| Edge | A relationship between states caused by an interaction. |
| YOLO | The object detector used to identify visual UI elements. |
| OCR | Optical character recognition used to identify text regions. |
| Seraphine | The grouping and semantic processing layer that combines detections and produces element descriptions. |
| Gemini | Optional external multimodal analysis used to enrich grouped detections with names and descriptions. |

## High-level workflow

```text
Desktop application
        |
        v
Launch, focus, and capture application window
        |
        v
YOLO detection + OCR detection
        |
        v
Bounding-box merge and stable IDs
        |
        v
Seraphine grouping and visual summaries
        |
        +--> Optional Gemini semantic enrichment
        |
        v
Create or update fDOM state
        |
        v
Choose a pending node -> click -> compare screenshots
        |
        v
Create a new state/edge, mark the node, save progress
```

The exploration loop is depth-first by default. Before an interaction, the tool captures a screenshot. It clicks the selected node using the configured click strategy, captures the result, compares the before and after images, and either records a new state or marks the element as non-changing/non-interactive. Navigation and backtracking helpers can return to an earlier state when a node belongs to another part of the graph.

## Repository layout

```text
.
|- apps/                         Generated artifacts per explored application
|  |- <app-name>/
|     |- fdom.json               Persistent functional DOM
|     |- metadata.json           Run and folder metadata
|     |- screenshots/            State and interaction screenshots
|     |- crops/                  Element crops
|     |- templates/              Optional launch templates
|     |- diffs/                  Visual differences between states
|- models/                       Local ONNX model files
|- images/                       Input screenshots and image assets
|- utils/
|  |- fdom/                      Exploration, interaction, state, and navigation code
|  |- seraphine_pipeline/        Detection, grouping, visualization, and export code
|  |- gui_controller.py          Windows window and mouse/keyboard helpers
|  |- seraphine.py               Single-image pipeline entry point
|- dump_code.py                  Utility for exporting Python source for inspection
|- test.py                       Manual Windows process/window launch diagnostic
|- pyproject.toml                Python project metadata and dependencies
|- uv.lock                       Locked dependency versions
```

## Requirements

- Windows, because the project uses Windows window handles, process inspection, and desktop input APIs.
- Python 3.11 or newer.
- `uv` for the commands shown below, or an equivalent Python environment manager.
- A display accessible to the process. The default configuration targets screen 1.
- The required local ONNX model files in `models/`.
- A compatible application executable for interactive exploration.
- Optional: a Gemini API key supplied through the environment when Gemini analysis is enabled.

The dependency manifest includes ONNX Runtime GPU. A compatible GPU/runtime setup is recommended. If GPU inference is unavailable, adjust the dependency and detector setup for the CPU environment before running the pipeline.

## Installation

From the repository root:

```powershell
uv sync
```

Activate the environment when using commands outside `uv run`:

```powershell
.\\.venv\\Scripts\\Activate.ps1
```

Before running a detector, verify that the configured model paths exist. Model binaries are intentionally ignored by Git and should be obtained through the project's approved model-distribution process. Do not commit model credentials, API keys, or private application paths.

## Secure configuration

There are two main configuration files:

- `utils/fdom/fdom_config.json` controls screen capture, storage, exploration, navigation, state tracking, retries, and visual comparison.
- `utils/seraphine_pipeline/config.json` controls YOLO/OCR paths and thresholds, grouping, visualizations, output location, and Gemini behavior.

Gemini reads `GEMINI_API_KEY` from the environment. Keep the value outside source control. A local `.env` file may be used because `.env` is ignored by Git:

```text
GEMINI_API_KEY=replace-with-your-local-secret
```

Do not paste a real key into this README, a config file, a command history, screenshots, generated JSON, or an issue. Set `gemini_enabled` to `false` when semantic cloud enrichment is not required; local detection and grouping can still be used.

## Running the image pipeline

The Seraphine pipeline accepts an image and runs detection, OCR, merging, grouping, optional Gemini analysis, JSON export, and visualizations.

```powershell
uv run python utils/seraphine.py --image "path\to\screenshot.png"
```

When no image is supplied, the pipeline uses the default configured image path. The pipeline writes its configured artifacts to `outputs/` in debug mode. The synchronous Python API is also available:

```python
from utils.seraphine import process_image_sync

result = process_image_sync(r"path\to\screenshot.png")
```

The returned result includes detection results, Seraphine analysis, optional Gemini results, grouped image paths, visualization paths, the exported JSON path, and total processing time.

## Creating an fDOM through interactive exploration

Use the fDOM creator with the full path to the executable you want to explore:

```powershell
uv run python utils/fdom/fdom_creator.py "C:\path\to\application.exe"
```

The creator:

1. Selects the configured display.
2. Launches the application and waits for its window.
3. Creates an application-specific folder under `apps/`.
4. Captures the initial window screenshot.
5. Builds the `root` fDOM state with detected nodes.
6. Displays pending nodes for manual selection.
7. Clicks a selected node and compares screenshots.
8. Adds discovered states and transitions to `fdom.json`.
9. Saves progress so an interrupted exploration can be resumed.

At the prompt, enter a node number or a node ID. Enter `skip` to record a manual description without clicking, or `exit` to stop. Existing fDOM data is loaded automatically when the application folder already contains `fdom.json`.

## Inspecting and testing interactions

The interaction engine can be used directly for an application or an existing session:

```powershell
uv run python utils/fdom/element_interactor.py --app-name "path\to\application.exe" --interactive
```

Useful options include:

```text
--click-node <node-id>   Click one specific node
--list-pending           List nodes that still need exploration
--manual-click           Use persistent manual click mode
```

The repository also contains a small Windows launch diagnostic for checking visible windows and process discovery:

```powershell
uv run python test.py
```

That diagnostic currently targets a locally installed image-editing application in its source code. Update the local path before using it; never replace it with a private or credential-bearing value in committed documentation.

## fDOM output

An application directory normally contains:

```text
apps/<app-name>/
|- fdom.json
|- metadata.json
|- screenshots/
|- crops/
|- diffs/
|- templates/
```

The fDOM root object includes the application name, creation timestamp, navigation tree, `states`, and `edges`. Each state records its parent, triggering element, screenshot, timestamps, and a `nodes` collection. A node commonly includes:

- `bbox`: `[x1, y1, x2, y2]` coordinates in the captured application image.
- `g_icon_name` and `g_brief`: semantic name and description.
- `g_enabled` and `g_interactive`: inferred interaction properties.
- `type` and `source`: detector classification and origin.
- `group`, `m_id`, `y_id`, and `o_id`: grouping and detector tracking IDs.
- `status`: pending, explored, or non-interactive state.
- `interactivity`: the resulting state and interaction type when available.

Because coordinates and screenshots are tied to window layout, changing display scaling, application theme, window size, or application version can change detection results. Treat generated fDOM data as an observed run, not as a universal contract for every machine.

## Analyzing an existing fDOM

The analyzer prints state, node, edge, node-type, duplicate, and crop statistics:

```powershell
uv run python utils/fdom/fdom_analyzer.py --fdom "apps\<app-name>\fdom.json"
```

This is useful for finding incomplete exploration, repeated detections, unusually large states, and duplicate crops.

## Configuration guidance

For a first local run, review these settings before launching an application:

- `capture.default_screen` and `capture.screen_selection_prompt` for the target monitor.
- `storage.base_directory` and the application folder names for generated artifacts.
- YOLO and OCR model paths in the Seraphine configuration.
- Detection thresholds if elements are missed or too many false positives appear.
- `gemini_enabled` and the prompt path if semantic enrichment is needed.
- Exploration retry and timeout values for slower applications.
- Debug and visualization switches when diagnosing a detection problem.

Keep generated screenshots, crops, logs, and model files out of commits unless they are intentionally curated, because they may contain private application data or machine-specific information.

## Troubleshooting

**The application window is not found**

- Confirm the executable path exists and launches normally.
- Check that the application opens on the configured display.
- Allow the application enough time to start and review the launch timeout settings.
- Avoid running the target application with a different privilege level when Windows blocks window discovery or input.

**No elements are detected**

- Confirm both detector model files exist at the configured paths.
- Check the screenshot dimensions and image format.
- Review YOLO confidence, OCR threshold, and merge IoU settings.
- Run with debug visualizations enabled to inspect raw and merged detections.

**Gemini analysis fails**

- Confirm `google-genai` is installed through `uv sync`.
- Set `GEMINI_API_KEY` only in the local environment.
- Confirm Gemini is enabled in the pipeline configuration and the prompt file exists.
- Disable Gemini to continue with local detection and Seraphine grouping.

**A session resumes with unexpected nodes**

- Inspect the application's existing `fdom.json`.
- Keep the application window size, display scale, theme, and startup state consistent.
- Start a fresh application folder when the application version or visual layout has changed substantially.

## Development notes

The code is organized around small responsibilities:

- `AppController` launches applications, locates windows, positions them, and creates artifact folders.
- `ScreenManager` and screenshot helpers capture the target window.
- YOLO, OCR, and `BBoxMerger` produce and reconcile visual detections.
- `FinalSeraphineProcessor` groups related detections.
- Gemini integration adds optional semantic labels and descriptions.
- `StateManager` persists states, nodes, status, and graph data.
- `ClickEngine`, `NavigationEngine`, and `VisualDiffer` execute and validate interactions.
- `FDOMCreator` coordinates the complete interactive workflow.

When changing behavior, keep generated paths configurable, preserve the fDOM schema, and validate changes with a small local screenshot or a controlled test application before exploring a large application.

## Privacy and security

This project can capture application windows and send selected grouped images to an external model provider when Gemini is enabled. Review screenshots and prompts before processing them. Do not use the tool on confidential data without authorization. Keep API keys, private executable paths, internal URLs, passwords, tokens, and generated sensitive artifacts out of source control.

## License

No license is declared in the current repository. Add the intended license before distributing the project.
