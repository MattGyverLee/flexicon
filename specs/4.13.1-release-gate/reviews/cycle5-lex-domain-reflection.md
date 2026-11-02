# Cycle 5 domain reflection (read-only)

Method: pythonnet reflection on SIL.LCModel plus read-only opens of 184 of 202 projects on this machine (18 failed to open, not investigated). Scripts are in the scratchpad (survey.py, s2.py, s3.py, s4.py).

## Q1 (#830 implementers)
- Reflected: IMoAffixForm.InflectionClassesRC has exactly two concrete implementers, MoAffixAllomorph and MoAffixProcess. MoStemAllomorph is the only concrete IMoStemAllomorph. The metadata cache confirms the field is owned by MoAffixForm (id 5028001) for both affix classes.
- Reflected/read: the resolver at AllomorphOperations.py:2215-2218 casts only MoStemAllomorph and MoAffixAllomorph. MoAffixProcess is NOT cast, so the field is unreachable on it.
- Consequence: retargeting to affix allomorphs covers MoAffixAllomorph only. Either accept that and document it, or add an IMoAffixProcess branch. Data-observed: procwithIC is 0 across every project (see Q2).

## Q2 (#830 semantics)
- Reflected: stems have no InflectionClasses field. MoStemMsa has InflectionClass (id 5001003, an atomic reference), and MoStemAllomorph has no such field.
- Data-observed: SpanishParsing has 16 stem MSAs with InflectionClassRA set. Four affix allomorphs sampled there carry classes such as ['-ir','-ar','-er'], and all are owned by LexEntry. These are verb conjugation classes, which fits "occurs only with stems of these classes".
- Not verified: the UI label "Inflection Classes". MetaDataCache.GetFieldLabel returned None. This part is FAIL: unverified by reflection.
- Counts: Sena 3 has 145 affix allomorphs and 0 with non-empty InflectionClassesRC. 15 projects have some, 113 allomorphs in total, for example SpanishParsing 15, French-FLExTrans-Demo2025 15, Spanish-FLExTrans-Demo2025/Exp4/Exp5 12 each, Ejagham W Mini 7, Aweti 4, Mbugwe LizzieHC practice 3. 32 projects have MoAffixProcess, and none has InflectionClassesRC set (0).
- Consequence: Sena 3 cannot serve as the live fixture. Use SpanishParsing read-only, or create a class in a sandbox.

## Q3 (#831 audio path)
- Reflected: ILexExampleSentence members are Example (IMultiString), Reference, TranslationsOC, PublishIn, DoNotPublishInRC and LiftResidue. It has no owned media object. By contrast ILexPronunciation has MediaFilesOS, and ICmMedia has Label and MediaFileRA.
- Data-observed, Xinaliq: 17 examples have a non-empty alternative in kjj-Zxxx-x-audio. Sample value: '636124083070919808A LexExampleSentence.wav'. The audio writing-system alternative holds a bare file name; the sampled examples are owned by LexSense.
- Not verified: whether that file sits in LinkedFiles/AudioVisual. In this copy it is absent (exists=False under Xinaliq\LinkedFiles\AudioVisual).
- Consequence: the confirmed attach path is "audio WS alternative holding a file name". No other media path was found on an example. Withdrawing MediaFilesOS-style methods is justified.

## Q4 (#831 fixtures)
- Target and Sena 3 have no audio writing system (data-observed: audioWS=[]).
- Audio writing systems exist in French-FLExTrans-Demo2025, GT-Sandbox-58, Tlachichilco Tepehua (+NT Noparse, +Speedtest) and Xinaliq.
- Only Xinaliq has examples with a non-empty audio alternative (17). Tlachichilco has 0.
- Consequence: a live fixture for a rebuild would have to be Xinaliq (read-only) or a sandbox where an audio writing system is added.

## Q5 (#832 IConstChartRow, reflected)
- Members: CellsOS (owning sequence), ClauseType (ClauseTypes enum), StartDependentClauseGroup (bool), EndDependentClauseGroup (bool), EndParagraph (bool), EndSentence (bool), Label (ITsString), Notes (ITsString).
- ClauseTypes values: Normal, Dependent, Song, Speech.
- Its base interfaces are only ICmObject and ICmObjectOrId.

## Q6 (#832 real chart data)
- Charts exist in about 13 projects. Analysed: Ngoreme, Ngoreme Johnny, Mbugwe Lizzie, Xinaliq, Tlachichilco Tepehua, Sena 3 and blx-flex.
- Referenced rows: ClauseType is Dependent, Speech or Song. It is Normal only once (Ngoreme Johnny), against hundreds of referenced rows.
- Group flags (Ngoreme, 372 references): 43 Dependent rows are Start=True/End=True. Multi-row groups carry Start=True on the first row and End=True on the last. Middle rows are False/False.
- Contiguity: every marker's referenced rows form a contiguous run in the same chart. Most follow the marker's row; some include or precede it.
- Consequence: writing DependentClausesRS alone leaves referenced rows as Normal/False/False. That state is essentially never observed (1 case). So the setter should also set ClauseType and the Start/End group flags, or at least validate the rows and warn.

## Q7 (cast_to_concrete on CmMedia)
- Data-observed: cast_to_concrete on an ICmObject from ObjectRepository.GetObject(hvo) of a CmMedia (Xinaliq pronunciation media) returns ICmObject, and hasattr(MediaFileRA) is False.
- An explicit ICmMedia(obj).MediaFileRA works ('AudioVisual\6.8.5.5. CREDIT.KJJ.Qurban. bank.wav').
- If the object comes from MediaFilesOS it is already typed ICmMedia, so the cast is a no-op there.
- grep: ICmMedia appears 0 times in lcm_casting.py (confirmed absent).
- Pronunciation media exists in Xinaliq (445), Tlachichilco (220) and Mbugwe Lizzie (1672).
