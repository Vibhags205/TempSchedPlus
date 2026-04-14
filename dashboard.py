from collections import Counter
from pathlib import Path

import streamlit as st

import cold_pipeline
import config
import prediction
import scheduler


st.set_page_config(page_title="TempSched+", page_icon="🌡️", layout="wide")


def _list_files(path: Path):
	return sorted([item.name for item in path.iterdir() if item.is_file()])


def _count_bytes(path: Path):
	return sum(item.stat().st_size for item in path.iterdir() if item.is_file())


def _render_metric(label, value, caption):
	st.markdown(
		f"""
		<div class="metric-card">
			<div class="metric-label">{label}</div>
			<div class="metric-value">{value}</div>
			<div class="metric-caption">{caption}</div>
		</div>
		""",
		unsafe_allow_html=True,
	)


st.markdown(
	"""
	<style>
		.stApp {
			background:
				radial-gradient(circle at top left, rgba(69, 123, 157, 0.20), transparent 28%),
				radial-gradient(circle at top right, rgba(241, 250, 238, 0.55), transparent 24%),
				linear-gradient(180deg, #f6f7fb 0%, #edf2f7 100%);
			color: #102a43;
		}
		.hero {
			padding: 1.4rem 1.6rem;
			border-radius: 24px;
			background: linear-gradient(135deg, #0f172a 0%, #16324f 55%, #1d4ed8 100%);
			color: white;
			box-shadow: 0 18px 50px rgba(15, 23, 42, 0.18);
			margin-bottom: 1rem;
		}
		.hero h1 {
			margin: 0;
			font-size: 2.1rem;
			letter-spacing: -0.03em;
		}
		.hero p {
			margin: 0.4rem 0 0;
			opacity: 0.9;
			max-width: 760px;
		}
		.metric-card, .panel-card {
			background: rgba(255, 255, 255, 0.82);
			border: 1px solid rgba(15, 23, 42, 0.08);
			border-radius: 20px;
			padding: 1rem 1.1rem;
			box-shadow: 0 12px 30px rgba(15, 23, 42, 0.08);
			backdrop-filter: blur(8px);
		}
		.metric-label {
			font-size: 0.82rem;
			text-transform: uppercase;
			letter-spacing: 0.08em;
			color: #64748b;
		}
		.metric-value {
			font-size: 2rem;
			font-weight: 700;
			margin-top: 0.2rem;
			color: #0f172a;
		}
		.metric-caption {
			font-size: 0.9rem;
			color: #475569;
		}
		.tier-title {
			font-size: 1.02rem;
			font-weight: 700;
			margin-bottom: 0.5rem;
			color: #0f172a;
		}
		.file-pill {
			display: inline-block;
			padding: 0.32rem 0.65rem;
			margin: 0.15rem 0.2rem 0.15rem 0;
			border-radius: 999px;
			background: #eff6ff;
			color: #1d4ed8;
			font-size: 0.82rem;
			border: 1px solid #bfdbfe;
		}
		.section-title {
			margin: 1rem 0 0.65rem;
			font-size: 1.08rem;
			font-weight: 700;
			color: #0f172a;
		}
		.small-note {
			color: #64748b;
			font-size: 0.9rem;
		}
	</style>
	""",
	unsafe_allow_html=True,
)

st.markdown(
	"""
	<div class="hero">
		<h1>TempSched+ Dashboard</h1>
		<p>Intelligent temperature-aware storage management across device, edge, and cloud with cold-data compression and encryption.</p>
	</div>
	""",
	unsafe_allow_html=True,
)

with st.sidebar:
	st.title("TempSched+")
	st.caption("Control panel")
	if st.button("Scan system + compress cold", use_container_width=True):
		cycle_result = cold_pipeline.process_files()
		st.session_state["scan_cycle"] = cycle_result
		st.session_state["rerun"] = True

	if st.button("Run scheduling cycle", use_container_width=True):
		scheduler.schedule()
		st.session_state["rerun"] = True

	st.divider()
	st.write("Storage tiers")
	st.write(f"Device: {len(_list_files(config.DEVICE))}")
	st.write(f"Edge: {len(_list_files(config.EDGE))}")
	st.write(f"Cloud: {len(_list_files(config.CLOUD))}")

if st.session_state.pop("rerun", False):
	st.rerun()

snapshot = scheduler.snapshot()
cloud_records = snapshot["cloud_records"]
temperature_store = snapshot["temperature_store"]
predicted_temperature = prediction.predict()
cloud_connected = len(cloud_records) > 0 or len(snapshot["cloud"]) > 0
pipeline_stats = cold_pipeline.get_pipeline_stats()
last_scan_cycle = st.session_state.get("scan_cycle")
scan_paths_count = len(getattr(config, "SCAN_PATHS", []))
scan_max_files = int(getattr(config, "SCAN_MAX_FILES", 1500))

metric_cols = st.columns(5)
with metric_cols[0]:
	_render_metric("Device Files", len(snapshot["device"]), f"{_count_bytes(config.DEVICE)} bytes")
with metric_cols[1]:
	_render_metric("Edge Files", len(snapshot["edge"]), f"{_count_bytes(config.EDGE)} bytes")
with metric_cols[2]:
	_render_metric("Cloud Archives", len(snapshot["cloud"]), f"{_count_bytes(config.CLOUD)} bytes")
with metric_cols[3]:
	_render_metric("Cold Records", pipeline_stats["compressed_records"], f"{len(snapshot['compressed'])} compressed copies")
with metric_cols[4]:
	_render_metric("Predicted Temp", predicted_temperature, "Random demo prediction for now")

storage_cols = st.columns(3)
with storage_cols[0]:
	_render_metric("Storage Saved", f"{pipeline_stats['saved_mb']} MB", "Total bytes saved by cold compression")
with storage_cols[1]:
	_render_metric("Scan Paths", scan_paths_count, "Documents/Downloads by default")
with storage_cols[2]:
	_render_metric("Max Scan Files", scan_max_files, "Per scan cycle")

st.markdown(
	"""
	<div class='panel-card'>
		<div class='tier-title'>Cloud Connection Status</div>
		<div class='small-note'>This project uses a local cloud simulation folder right now. When a file is classified as COLD, it is compressed, encrypted, copied into the cloud folder, and written to the cloud index.</div>
	</div>
	""",
	unsafe_allow_html=True,
)

st.write(f"Cloud connected: {'Yes' if cloud_connected else 'Not yet'}")

if last_scan_cycle:
	st.success(
		f"Last scan: scanned {last_scan_cycle['scanned']} files, cold={last_scan_cycle['cold']}, newly compressed={last_scan_cycle['compressed']}, saved={round(last_scan_cycle['saved_bytes'] / (1024 * 1024), 2)} MB"
	)

st.markdown("<div class='section-title'>Hot Data Status</div>", unsafe_allow_html=True)
if last_scan_cycle:
	hot_count = int(last_scan_cycle.get("hot", 0))
	warm_count = int(last_scan_cycle.get("warm", 0))
	cold_count = int(last_scan_cycle.get("cold", 0))
	hot_files = last_scan_cycle.get("hot_files", [])

	hot_cols = st.columns(3)
	with hot_cols[0]:
		_render_metric("Hot (last scan)", hot_count, "Frequently accessed files")
	with hot_cols[1]:
		_render_metric("Warm (last scan)", warm_count, "Moderate access files")
	with hot_cols[2]:
		_render_metric("Cold (last scan)", cold_count, "Rarely accessed files")

	if hot_files:
		st.write("Hot files detected in last scan:")
		st.dataframe(
			[{"Hot File Path": path} for path in hot_files],
			use_container_width=True,
			hide_index=True,
		)
	else:
		st.info("No hot files detected in the last scan cycle.")

	classified_rows = last_scan_cycle.get("classified", [])
	if classified_rows:
		st.write("Recent classification samples:")
		st.dataframe(
			[
				{
					"Path": item.get("path", ""),
					"Decision": str(item.get("decision", "")).upper(),
					"Predicted Temp": item.get("predicted_temperature", ""),
					"Size (KB)": round(float(item.get("size", 0)) / 1024, 2),
				}
				for item in classified_rows[:50]
			],
			use_container_width=True,
			hide_index=True,
		)
else:
	st.info("Run 'Scan system + compress cold' to populate hot/warm/cold classification data.")

st.markdown("<div class='section-title'>Tier Overview</div>", unsafe_allow_html=True)
tier_cols = st.columns(3)
with tier_cols[0]:
	st.markdown("<div class='panel-card'><div class='tier-title'>Device Tier</div>", unsafe_allow_html=True)
	if snapshot["device"]:
		st.markdown("".join(f"<span class='file-pill'>{name}</span>" for name in snapshot["device"]), unsafe_allow_html=True)
	else:
		st.write("No active files in device tier.")
	st.markdown("</div>", unsafe_allow_html=True)
with tier_cols[1]:
	st.markdown("<div class='panel-card'><div class='tier-title'>Edge Tier</div>", unsafe_allow_html=True)
	if snapshot["edge"]:
		st.markdown("".join(f"<span class='file-pill'>{name}</span>" for name in snapshot["edge"]), unsafe_allow_html=True)
	else:
		st.write("No files staged at edge.")
	st.markdown("</div>", unsafe_allow_html=True)
with tier_cols[2]:
	st.markdown("<div class='panel-card'><div class='tier-title'>Cloud Tier</div>", unsafe_allow_html=True)
	if snapshot["cloud"]:
		st.markdown("".join(f"<span class='file-pill'>{name}</span>" for name in snapshot["cloud"]), unsafe_allow_html=True)
	else:
		st.write("No cold archives stored in cloud.")
	st.markdown("</div>", unsafe_allow_html=True)

st.markdown("<div class='section-title'>Cold Data Pipeline</div>", unsafe_allow_html=True)
pipeline_cols = st.columns([1.15, 0.85])
with pipeline_cols[0]:
	st.markdown(
		"""
		<div class='panel-card'>
			<div class='tier-title'>Cold Archive Flow</div>
			<div class='small-note'>Files classified as COLD are compressed, encrypted, indexed, and copied to cloud storage.</div>
			<ol>
				<li>Device file is scheduled after temperature decay.</li>
				<li>Cold file is compressed with gzip.</li>
				<li>Compressed payload is encrypted with Fernet.</li>
				<li>Final encrypted bundle is stored in cloud and indexed.</li>
			</ol>
		</div>
		""",
		unsafe_allow_html=True,
	)
with pipeline_cols[1]:
	st.markdown("<div class='panel-card'><div class='tier-title'>Temperature Snapshot</div>", unsafe_allow_html=True)
	if temperature_store:
		temp_counts = Counter(scheduler.classify_temperature(temp) for temp in temperature_store.values())
		st.write({tier: temp_counts.get(tier, 0) for tier in ["HOT", "WARM", "COLD"]})
		st.json({name: round(value, 2) for name, value in temperature_store.items()})
	else:
		st.write("No temperature history yet. Run a scheduling cycle to populate this panel.")
	st.markdown("</div>", unsafe_allow_html=True)

st.markdown("<div class='section-title'>Predicted Temperature</div>", unsafe_allow_html=True)
st.markdown(
	f"""
	<div class='panel-card'>
		<div class='tier-title'>Next Access Forecast</div>
		<div class='metric-value'>{predicted_temperature}</div>
		<div class='small-note'>This is the current predicted temperature value returned by the prediction module.</div>
	</div>
	""",
	unsafe_allow_html=True,
)

st.markdown("<div class='section-title'>Cloud Index</div>", unsafe_allow_html=True)
if cloud_records:
	st.dataframe(
		[
			{
				"File": item["filename"],
				"Cloud Object": item["cloud_object"],
				"Temperature": item["temperature"],
				"Size (bytes)": item["size_bytes"],
				"Stored At": item["stored_at"],
			}
			for item in cloud_records
		],
		use_container_width=True,
		hide_index=True,
	)
else:
	st.info("Cloud index is empty. Cold files will appear here after the first scheduling cycle.")

st.markdown("<div class='section-title'>Recent Cold Compression Records</div>", unsafe_allow_html=True)
if pipeline_stats["recent"]:
	st.dataframe(
		[
			{
				"Original Path": item.get("original_path", ""),
				"Decision": item.get("decision", ""),
				"Predicted Temp": item.get("predicted_temperature", ""),
				"Saved (KB)": round(item.get("saved_bytes", 0) / 1024, 2),
				"Compressed Path": item.get("compressed_path", ""),
			}
			for item in reversed(pipeline_stats["recent"])
		],
		use_container_width=True,
		hide_index=True,
	)
else:
	st.info("No cold files compressed from system scan yet.")
