I want to enhance the code with oop and design patterns but don't remove or change anything: 
# Path to your speaker files (Update this to the actual path where your audio samples are stored)
speaker_base_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "samples")
print(speaker_base_path)TTS_LANGUAGES = ["en", "es", "fr", "de", "it", "pt", "pl", "tr", "ru", "nl", "cs", "ar", "zh-cn", "ja", "hu", "ko"] 
GENDERS = ["Female", "Male"]
FEMALE_SPEAKERS = ["Aisha", "Fatima", "Alyaa", "Angel", "Youstina"]
MALE_SPEAKERS = ["Omar", "Ali"]
AUDIO_FORMATS = ["normal", "16kbps_mono_pcm_wav", "32kbps_stereo_aac_m4a", "16kbps_mono_opus_opus", "64kbps_mono_mp3",
                 "8kbps_mono_ulaw_wav"]TTS_LLM = ["EFTTS" , "EFTTSV2"]
@app.on_event("startup")
def load_models():
    global tts
    

    device = "cuda" if torch.cuda.is_available() else "cpu"
    
    tts = TTS(model_name="xtts_v2.0.2", gpu=(device == "cuda"))# Function to split text into sentences 
def split_text_to_sentences(text):
    cleaned_text = re.sub(r'\s+', ' ', text).replace('\n', ' ').strip()
    sentence_boundaries = re.compile(r'(?<=[.!?]) +')
    sentences = sentence_boundaries.split(cleaned_text)
    return [sentence.strip() for sentence in sentences if sentence.strip()]

# Function to get speaker file path
def get_speaker_file(gender, speaker):
    if gender not in GENDERS:
        append_log_message("Invalid gender selected.", log_dir, base_filename, max_bytes, max_files)

        raise ValueError("Invalid gender selected.")
    if gender == "Female":
        if speaker not in FEMALE_SPEAKERS:
            append_log_message("Invalid female speaker selected.", log_dir, base_filename, max_bytes, max_files)
            raise ValueError("Invalid female speaker selected.")
        speaker_files = {
            "Aisha": "Female.wav",
            "Fatima": "Female_1.wav",
            "Alyaa": "Female_2.wav",
            "Angel": "Female_3.wav",
            "Youstina": "Female_4.wav",
        }
    else:
        if speaker not in MALE_SPEAKERS:
            append_log_message("Invalid male speaker selected.", log_dir, base_filename, max_bytes, max_files)
            raise ValueError("Invalid male speaker selected.")
        speaker_files = {
            "Omar": "Male.wav",
            "Ali": "Male_1.wav",
        }

    speaker_file = os.path.join(speaker_base_path, speaker_files.get(speaker))
    if not os.path.exists(speaker_file):
        raise FileNotFoundError(f"Speaker file '{speaker_file}' not found.")

    return speaker_file
# "16kbps_mono_pcm_wav", "32kbps_stereo_aac_m4a", "16kbps_mono_opus_opus", "64kbps_mono_mp3", "8kbps_mono_ulaw_wav"
def export_audio_formats(combined_audio, format):
    buffer = BytesIO()
    if format == "16kbps_mono_pcm_wav":
        # Export to 16kbps, mono, PCM .wav
        buffer = BytesIO()
        pcm_wav = combined_audio.set_frame_rate(16000).set_channels(1)
        pcm_wav.export(buffer, format="wav", codec="pcm_s16le")
        buffer.seek(0)
    if format == "32kbps_stereo_aac_m4a":
        # Export to 32kbps, stereo, AAC .m4a
        buffer = BytesIO()
        aac_m4a = combined_audio.set_frame_rate(32000).set_channels(2)
        aac_m4a.export(buffer, format="mp3", bitrate="32k")
        buffer.seek(0)
    if format == "16kbps_mono_opus_opus":
        # Export to 16kbps, mono, Opus .opus
        buffer = BytesIO()
        opus_audio = combined_audio.set_frame_rate(16000).set_channels(1)
        opus_audio.export(buffer, format="opus", bitrate="16k")
        buffer.seek(0)
    if format == "64kbps_mono_mp3":
        # Export to 64kbps, mono, MP3 .mp3
        buffer = BytesIO()
        mp3_audio = combined_audio.set_frame_rate(64000).set_channels(1)
        mp3_audio.export(buffer, format="mp3", bitrate="64k")
        buffer.seek(0)
    if format == "8kbps_mono_ulaw_wav":
        # Export to 8kbps, mono, u-law PCM .wav
        buffer = BytesIO()
        ulaw_wav = combined_audio.set_frame_rate(8000).set_channels(1)
        ulaw_wav.export(buffer, format="wav", codec="pcm_mulaw", bitrate="8k")
        buffer.seek(0)
    return buffer




# TTS API Endpoint Container
@app.post("/EFTTS/generate-voice", summary="ExpertFlow TTS Container API")
async def generate_voice(
        request: Request,
        client_ip: str = Form("Unknown", description="Client IP for requester"),
        language: str = Form(..., description="Language code (e.g., 'ar', 'en')"),
        gender: str = Form("Male", description="Gender ('Female' or 'Male')"),
        speaker: str = Form("Omar", description="Speaker name based on gender"),
        text: str = Form(..., description="Text to convert to speech"),
        format: str = Form("normal",
                           description="Audio format for output (16kbps_mono_pcm_wav, 32kbps_stereo_aac_m4a, 16kbps_mono_opus_opus, 64kbps_mono_mp3, 8kbps_mono_ulaw_wav)"),
        allowance: str = Form("Yes", description="Allowance to generate voice (Yes or No)") , # Add allowance parameter
        llm: str = Form(..., description="LLM (e.g., 'EFTTS' )"),
):
    # Check allowance before proceeding
    if allowance.lower() == "no":
        append_log_message(
            f"Request from {client_ip} rejected due to exceeding the concurrent request limit.",
            log_dir, base_filename, max_bytes, max_files)

        append_sql_log(client_ip, "POST", "/generate-voice",
                       "No-duration",
                       "403", "no_content",
                       "License limit for concurrent requests exceeded", int(0))
        raise HTTPException(status_code=403, detail="License limit for concurrent requests exceeded")

    else:
        start_time = time.time()
        try:
            # Validate inputs
            if llm not in TTS_LLM:
                append_log_message(
                    f"Request from {client_ip} not completed because of Entered unsupported LLM {llm} , So User was told to Choose from {TTS_LLM} .",
                    log_dir, base_filename, max_bytes, max_files)
                append_sql_log(client_ip, "POST", "/generate-voice",
                               "No-duration - unsupported llm",
                               "400", "no_content",
                               f"unsupported llm {llm}.",
                               0)
                print(
                    f"### Request from {client_ip} not completed because of Entered unsupported llm {llm} , So User was told to Choose from {TTS_LLM} .")
                raise HTTPException(status_code=400, detail=f"Unsupported llm. Choose from {TTS_LLM}.")



            if language not in TTS_LANGUAGES:
                append_log_message(
                    f"Request from {client_ip} not completed because of Entered unsupported language {language} For Our TTS, So User was told to Choose from {TTS_LANGUAGES} .",
                    log_dir, base_filename, max_bytes, max_files)
                append_sql_log(client_ip, "POST", "/generate-voice",
                               "No-duration - unsupported language",
                               "400", "no_content",
                               f"unsupported language {language}.",
                               0)
                print(
                    f"### Request from {client_ip} not completed because of Entered unsupported language {language} For Our TTS, So User was told to Choose from {TTS_LANGUAGES} .")
                raise HTTPException(status_code=400, detail=f"Unsupported language. Choose from {TTS_LANGUAGES}.")

            if gender not in GENDERS:
                append_log_message(
                    f"Request from {client_ip} not completed because of Entered unsupported gender {gender} , So User was told to Choose from {GENDERS} .",
                    log_dir, base_filename, max_bytes, max_files)
                append_sql_log(client_ip, "POST", "/generate-voice",
                               "No-duration - unsupported gender",
                               "400",
                               "no_content",
                               f"unsupported gender {gender} .",
                               0)
                print(
                    f"### Request from {client_ip} not completed because of Entered unsupported gender {gender} , So User was told to Choose from {GENDERS} .")
                raise HTTPException(status_code=400, detail=f"Unsupported gender. Choose from {GENDERS}.")

            if gender == "Female" and speaker not in FEMALE_SPEAKERS:
                append_log_message(
                    f"Request from {client_ip} not completed because of Entered unsupported famale speaker: {speaker} , So User was told to Choose from {FEMALE_SPEAKERS} .",
                    log_dir, base_filename, max_bytes, max_files)
                append_sql_log(client_ip, "POST", "/generate-voice",
                               "No-duration - unsupported female speaker",
                               "400",
                               "no_content",
                               f"unsupported famale speaker {speaker}",
                               0)
                print(
                    f"### Request from {client_ip} not completed because of Entered unsupported famale speaker: {speaker} , So User was told to Choose from {FEMALE_SPEAKERS} .")
                raise HTTPException(status_code=400,
                                    detail=f"Unsupported female speaker. Choose from {FEMALE_SPEAKERS}.")

            if gender == "Male" and speaker not in MALE_SPEAKERS:
                append_log_message(
                    f"Request from {client_ip} not completed because of Entered unsupported male speaker: {speaker} , So User was told to Choose from {MALE_SPEAKERS} .",
                    log_dir, base_filename, max_bytes, max_files)
                append_sql_log(client_ip, "POST", "/generate-voice",
                               "No-duration - unsupported male speaker",
                               "400",
                               "no_content",
                               f"unsupported male speaker {speaker}.",
                               0)
                print(
                    f"### Request from {client_ip} not completed because of Entered unsupported male speaker: {speaker} , So User was told to Choose from {MALE_SPEAKERS} .")
                raise HTTPException(status_code=400,
                                    detail=f"Unsupported male speaker. Choose from {MALE_SPEAKERS}.")

            if not text.strip():
                append_log_message(
                    f"Request from {client_ip} not completed because User didn't enter text .", log_dir,
                    base_filename, max_bytes, max_files)
                append_sql_log(client_ip, "POST", "/generate-voice",
                               "No-duration - no text entered",
                               "400",
                               "no_content",
                               f"User didn't enter text .",
                               0)
                print(
                    f"### Request from {client_ip} not completed because User didn't enter text .")
                raise HTTPException(status_code=400, detail="Text cannot be empty.")

            if format not in AUDIO_FORMATS:
                append_log_message(
                    f"Request from {client_ip} not completed because User entered unsupported format from these {AUDIO_FORMATS} .",
                    log_dir, base_filename, max_bytes, max_files)
                append_sql_log(client_ip, "POST", "/generate-voice",
                               "No-duration - unsupported format ",
                               "400",
                               "no_content",
                               f"{format} unsupported format. ",
                               0)
                raise HTTPException(status_code=400, detail=f"Unsupported format. Choose from {AUDIO_FORMATS}.")



            if llm == "EFTTS" :#and language not in TTS_LANGUAGES:
                # Get speaker file
                speaker_file = get_speaker_file(gender, speaker)
                characters_count = len(text)
                # Split text into sentences
                sentences = split_text_to_sentences(text)
                audio_segments = []

                for i, sentence in enumerate(sentences):
                    output_path = f"generated_output_{i}.wav"
                    # Configurations for male and female voices
                    if language == "ar" and gender == "Female":
                        temperature = 0.1
                        repetition_penalty = 50.5
                        top_k = 80
                        # Generate the TTS output
                        tts.tts_to_file(
                            text=sentence,
                            speaker_wav=speaker_file,
                            language=language,
                            file_path=output_path,
                            split_sentences=True,
                            temperature=temperature,
                            repetition_penalty=repetition_penalty,
                            top_k=top_k,
                            top_p=0.95,
                            speed=1.0
                        )
                    elif language == "ar" and gender == "Male":
                        temperature = 0.1
                        repetition_penalty = 10.5
                        top_k = 80
                        # Generate the TTS output
                        tts.tts_to_file(
                            text=sentence,
                            speaker_wav=speaker_file,
                            language=language,
                            file_path=output_path,
                            split_sentences=True,
                            temperature=temperature,
                            repetition_penalty=repetition_penalty,
                            top_k=top_k,
                            top_p=0.95,
                            speed=1.0
                        )
                    else:
                        # Generate the TTS output
                        tts.tts_to_file(
                            text=sentence,
                            speaker_wav=speaker_file,
                            language=language,
                            file_path=output_path,
                            split_sentences=True,
                        )
                    audio_segments.append(output_path)

                # Concatenate all audio segments
                combined_audio = AudioSegment.silent(duration=0)
                for audio_file in audio_segments:
                    combined_audio += AudioSegment.from_wav(audio_file)
                    os.remove(audio_file)  # Clean up individual files

                # Export combined audio to bytes
                buffer = BytesIO()
                if format == "normal":
                    # print("############## The voice is combining .... ")
                    combined_audio.export(buffer, format="wav")
                    buffer.seek(0)
                    # print("############## The voice is combined successfully .... ")
                else:
                    buffer = export_audio_formats(combined_audio, format)

                # Log the execution duration
                duration = time.time() - start_time
                request_content = {
                    'language': language,
                    'gender': gender,
                    'speaker': speaker,
                    'text': text,
                    'format': format
                }
                append_log_message(
                    f"Request from {client_ip} completed in {duration:.2f} seconds. \n request_content: {str(request_content)}",
                    log_dir, base_filename, max_bytes, max_files)
                append_sql_log(client_ip, "POST", "/generate-voice", duration, "200", request_content,
                               f"Voice generated successfully in format : {format}", characters_count)
                print(f"### Request from {client_ip} completed in {duration:.2f} seconds.")

                return StreamingResponse(buffer, media_type="audio/wav",
                                         headers={"Content-Disposition": "attachment; filename=generated_voice.wav"})
        except HTTPException as he:
            logging.error(f"HTTP Exception: {str(he.detail)}")
            return JSONResponse(content={
                "detail": he.detail
            }, status_code=he.status_code)

        except Exception as e:
            logging.error(f"Unexpected error: {str(e)}")
            return JSONResponse(content={
                "detail": f"An unexpected error occurred: {str(e)}"
            }, status_code=500)
