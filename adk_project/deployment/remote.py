import os
from absl import app
from absl import flags
from dotenv import load_dotenv
from google.cloud.aiplatform import reasoning_engines
from adk_project.agent import root_agent

FLAGS = flags.FLAGS

flags.DEFINE_string("project_id", None, "The Google Cloud project ID.")
flags.DEFINE_string("location", "us-central1", "The deployment location.")
flags.DEFINE_string("bucket", None, "The GCS bucket for staging.")
flags.DEFINE_string("user_id", "user", "A temporary user ID.")

def create() -> None:
    """Creates a new deployment."""
    # First wrap the agent in AdkApp
    app = reasoning_engines.AdkApp(
        agent=root_agent,
        enable_tracing=True,
    )

    # Now deploy to Agent Engine
    remote_app = reasoning_engines.create(
        agent_engine=app,
        requirements=[
            "google-cloud-aiplatform[adk,agent_engines]",
        ],
        extra_packages=["."],
        project=FLAGS.project_id,
        location=FLAGS.location,
        staging_bucket=FLAGS.bucket,
    )
    print(f"Created remote app: {remote_app.resource_name}")

def main(argv=None):
    """Main function that can be called directly or through app.run()."""
    # Parse flags first
    if argv is None:
        argv = FLAGS(argv)
    else:
        argv = FLAGS(argv)
    
    load_dotenv()

    # Now we can safely access the flags
    project_id = FLAGS.project_id if FLAGS.project_id else os.getenv("GOOGLE_CLOUD_PROJECT")
    location = FLAGS.location if FLAGS.location else os.getenv("GOOGLE_CLOUD_LOCATION")
    bucket = FLAGS.bucket if FLAGS.bucket else os.getenv("GOOGLE_CLOUD_STAGING_BUCKET")

    if not project_id:
        print("Missing required environment variable: GOOGLE_CLOUD_PROJECT")
        return
    if not location:
        print("Missing required environment variable: GOOGLE_CLOUD_LOCATION")
        return
    if not bucket:
        print("Missing required environment variable: GOOGLE_CLOUD_STAGING_BUCKET")
        return
    
    create()

if __name__ == "__main__":
    app.run(main) 