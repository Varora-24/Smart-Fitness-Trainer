# ================================================================
#  tests/test_webcam_retry.py  –  Tests for webcam frame retries
# ================================================================

from unittest.mock import patch, MagicMock
import numpy as np
import main

def _setup_mock_pipeline(mock_pipeline_cls):
    mock_pipeline_inst = mock_pipeline_cls.return_value
    mock_pipeline_inst.current_key = "squats"
    mock_pipeline_inst.tracker = MagicMock()
    mock_pipeline_inst.tracker.avg_symmetry = 90.0
    mock_pipeline_inst.tracker.avg_form = 95.0
    
    mock_pipeline_inst.session = MagicMock()
    mock_pipeline_inst.session.total_calories = 10.0
    mock_pipeline_inst.session.elapsed = 15.0
    mock_pipeline_inst.session.reps_per_minute = 4.0
    mock_pipeline_inst.session.summary.return_value = {
        "total_reps": 3,
        "clean_reps": 2,
        "bad_reps": 1,
        "calories": 10.0,
        "duration_secs": 15.0,
        "avg_rep_score": 80.0,
        "reps_per_min": 4.0
    }
    mock_pipeline_inst.inserted_rep_ids = [1, 2, 3]
    return mock_pipeline_inst

@patch("main.cv2.VideoCapture")
@patch("main.FramePipeline")
@patch("main.db")
@patch("main.show_summary")
@patch("main.cv2.imshow")
@patch("main.cv2.waitKey")
@patch("main.argparse.ArgumentParser.parse_args")
def test_webcam_resilience_loop(
    mock_parse_args, mock_wait_key, mock_imshow, mock_show_summary,
    mock_db, mock_pipeline_cls, mock_video_capture_cls
):
    # Setup args: --source webcam
    args_mock = MagicMock()
    args_mock.source = "webcam"
    args_mock.verbose = False
    mock_parse_args.return_value = args_mock

    # Mock VideoCapture to fail 5 times then return success frame once, then fail and exit (after 30 fails)
    mock_cap = MagicMock()
    mock_cap.isOpened.return_value = True
    
    dummy_frame = np.zeros((720, 1280, 3), dtype=np.uint8)
    
    read_responses = (
        [(False, None)] * 5 +
        [(True, dummy_frame)] +
        [(False, None)] * 30
    )
    mock_cap.read.side_effect = read_responses
    mock_video_capture_cls.return_value = mock_cap

    # Let waitKey just return a non-quit key (e.g. 255)
    mock_wait_key.return_value = 255

    # Mock pipeline attributes
    _setup_mock_pipeline(mock_pipeline_cls)

    # Call main
    main.main()

    # Assert that read() was called 5 (failures) + 1 (success) + 30 (fatal failures) = 36 times
    assert mock_cap.read.call_count == 36


@patch("main.cv2.VideoCapture")
@patch("main.FramePipeline")
@patch("main.db")
@patch("main.show_summary")
@patch("main.cv2.imshow")
@patch("main.cv2.waitKey")
@patch("main.argparse.ArgumentParser.parse_args")
def test_file_source_exits_immediately(
    mock_parse_args, mock_wait_key, mock_imshow, mock_show_summary,
    mock_db, mock_pipeline_cls, mock_video_capture_cls
):
    # Setup args: --source test.mp4
    args_mock = MagicMock()
    args_mock.source = "test.mp4"
    args_mock.verbose = False
    mock_parse_args.return_value = args_mock

    # Mock VideoCapture to fail on first read
    mock_cap = MagicMock()
    mock_cap.isOpened.return_value = True
    mock_cap.read.return_value = (False, None)
    mock_video_capture_cls.return_value = mock_cap

    # Mock pipeline attributes
    _setup_mock_pipeline(mock_pipeline_cls)

    # Call main
    main.main()

    # Assert that read() was called exactly 1 time and exited
    assert mock_cap.read.call_count == 1
