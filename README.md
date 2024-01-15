# Kubeflows Hub


## Repository Organization

Components are named with two pieces of critical information, and one piece of optional information:
1. A verb describing the action the component performs
2. Noun(s) describing the type of data the component operates on and/or the type of data that the component generates
    * Supply the most meaningful nouns only (e.g., generating "captions" sufficiently implies "images" as the source)
3. (Optional) Implmentation-specific details (e.g., algorithm, AI model, or cloud provider used)

As an example, we have [`generate-caption-blip2.yaml`](generate/generate-caption-blip2.yaml), which generates captions for images using the BLIP-2 model.  

Components are hierarchically organized by their verb, in the repository.

## Dependencies

When using this repository, use the raw YAML files from a release (rather than the main branch) to avoid breaking changes.

When writing components, `packages_to_install` dependencies should be pinned to a major version (and optionally pinned to minor or bug versions, if necessary).  As far as the Python version, components will be upgraded together and currently use the `python:3.11` base image.

## Usage

Most components use the standard Kubeflow `Artifact` system for handling inputs and outputs.  However, some components have an unknown (at compile time) number of `Input`s or `Output`s.  As of this writing, there is no support for input/output artifact aggregations like this, so we instead rely on filepaths on the local (container) filesystem.  Remote artifacts are then enabled via GCS, MinIO, etc. fusing (done by default on Vertex AI Pipelines). Use `Importer`s and the `Artifact`'s `uri` parameter, where required in your pipelines.  As long as a component initializes in a reasonable amount of time, fan-in and fan-out (e.g., `ParallelFor` and `Collected`) "map"-type operations to avoid n inputs, n outputs situations (where the aggregated artifacts limitation becomes an issue).

[Related GitHub Issue](https://github.com/kubeflow/pipelines/issues/1933)

`Artifact` metadata is usually only used to specify the mimeType of the artifact.  Consider following this precedent in your own components.

Cloud-specific components, such as for Vertex AI Batch Prediction (Google Cloud), generally assume that you are also running the pipeline on the cloud platform (Vertex AI Pipelines, in the previous example) and can use application default credentials and service accounts.  Examples:
1. The component for captioning with BLIP-2 can be ran anywhere
2. The component for transcribing with Google Speech-to-Text requires the use of Vertex AI Pipelines (or DIY Kubeflow on GKE/GCE)
3. The component for prompting against OpenAI (which does not have a cloud platform) models requires runtime specification of credentials

## Contributing

Issues, feature requests, and pull requests are always welcome!

## License

This project is licensed under either of [Apache License, Version 2.0](https://www.apache.org/licenses/LICENSE-2.0) or [MIT License](https://opensource.org/licenses/MIT) at your option.

[Apache License, Version 2.0](LICENSE-APACHE)

[MIT License](LICENSE-MIT)

Unless you explicitly state otherwise, any contribution intentionally submitted for inclusion in kubeflows-hub by you, as defined in the Apache-2.0 license, shall be dual licensed as above, without any additional terms or conditions.