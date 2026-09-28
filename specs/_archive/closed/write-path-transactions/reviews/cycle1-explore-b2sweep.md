# Cycle 1 explore B2s: unbracketed LCM mutations (no `with self._TransactionCM(...)`)

**Total methods in scope: 294**

Distribution: Lexicon 84, Grammar 59, Notebook 44, TextsWords 24, Discourse 21, Lists 14, (code root) 13, System 11, Scripture 9, Shared 9, Reversal 6

Method: AST scan of every `.py` under `flexicon/code/`. For each method of every class, any mutation node not lexically enclosed by a `with self._TransactionCM(...)` block is recorded. `_TransactionCM` is the only bracketing construct present in the source; `@OperationsMethod` was ignored. Line = `def` line of the method. Mutation kind lists the distinct indicators found outside the block (a method may also contain a bracketed block plus stray mutations - it is still listed). Pure delegations (`return self.LexEntry.Create(...)`), `TsStrBldr` builder calls and `SandboxGenericMSA` field assignments were excluded; see Ambiguous cases.

| File (path relative to flexicon/code) | Line | Class.Method | Mutation kind | Confidence |
| --- | --- | --- | --- | --- |
| BaseOperations.py | 516 | BaseOperations.Sort | .MoveTo | needs-review |
| BaseOperations.py | 613 | BaseOperations.MoveUp | .MoveTo | needs-review |
| BaseOperations.py | 709 | BaseOperations.MoveDown | .MoveTo | needs-review |
| BaseOperations.py | 806 | BaseOperations.MoveToIndex | .MoveTo | needs-review |
| BaseOperations.py | 891 | BaseOperations.MoveBefore | .MoveTo | needs-review |
| BaseOperations.py | 966 | BaseOperations.MoveAfter | .MoveTo | needs-review |
| BaseOperations.py | 1042 | BaseOperations.Swap | .MoveTo | needs-review |
| Discourse/ConstChartCellTagOperations.py | 58 | ConstChartCellTagOperations.Create | factory.Create | high |
| Discourse/ConstChartCellTagOperations.py | 102 | ConstChartCellTagOperations.Delete | .Delete | high |
| Discourse/ConstChartCellTagOperations.py | 165 | ConstChartCellTagOperations.SetMarker | prop assign (TagRA) | high |
| Discourse/ConstChartClauseMarkerOperations.py | 138 | ConstChartClauseMarkerOperations.Delete | .Delete | high |
| Discourse/ConstChartClauseMarkerOperations.py | 333 | ConstChartClauseMarkerOperations.AddDependentClause | .Add | high |
| Discourse/ConstChartMarkerOperations.py | 115 | ConstChartMarkerOperations.Delete | .Delete | high |
| Discourse/ConstChartMarkerOperations.py | 194 | ConstChartMarkerOperations.SetName | set_String | high |
| Discourse/ConstChartMarkerOperations.py | 217 | ConstChartMarkerOperations.SetDescription | set_String | high |
| Discourse/ConstChartMarkerOperations.py | 281 | ConstChartMarkerOperations.__GetOrCreateChartMarkers | prop assign (DiscourseDataOA); factory.Create; prop assign (ChartMarkersOA) | high |
| Discourse/ConstChartMovedTextOperations.py | 136 | ConstChartMovedTextOperations.Delete | .Delete | high |
| Discourse/ConstChartOperations.py | 183 | ConstChartOperations.Delete | .Delete | high |
| Discourse/ConstChartOperations.py | 347 | ConstChartOperations.SetName | set_String | high |
| Discourse/ConstChartOperations.py | 422 | ConstChartOperations.SetTemplate | prop assign (TemplateRA) | high |
| Discourse/ConstChartOperations.py | 526 | ConstChartOperations.__GetOrCreateDiscourse | factory.Create; prop assign (DiscourseDataOA) | high |
| Discourse/ConstChartRowOperations.py | 142 | ConstChartRowOperations.Delete | .Delete | high |
| Discourse/ConstChartRowOperations.py | 301 | ConstChartRowOperations.SetLabel | set_String | high |
| Discourse/ConstChartRowOperations.py | 376 | ConstChartRowOperations.SetNotes | set_String | high |
| Discourse/ConstChartWordGroupOperations.py | 148 | ConstChartWordGroupOperations.Delete | .Delete | high |
| Discourse/ConstChartWordGroupOperations.py | 297 | ConstChartWordGroupOperations.SetBeginSegment | prop assign (BeginSegmentRA) | high |
| Discourse/ConstChartWordGroupOperations.py | 369 | ConstChartWordGroupOperations.SetEndSegment | prop assign (EndSegmentRA) | high |
| Discourse/ConstChartWordGroupOperations.py | 442 | ConstChartWordGroupOperations.SetColumn | prop assign (ColumnRA) | high |
| FLExProject.py | 3420 | FLExProject.LexiconSetFieldText | SetString; set_String | needs-review |
| FLExProject.py | 3464 | FLExProject.LexiconClearField | SetString; set_String | needs-review |
| FLExProject.py | 3637 | FLExProject.LexiconSetListFieldMultiple | Replace | needs-review |
| FLExProject.py | 3978 | FLExProject.LexiconDeleteObject | .Remove; .Delete | high |
| FLExProject.py | 4245 | FLExProject.LexiconSetComplexFormType | Clear | needs-review |
| FLExProject.py | 4266 | FLExProject.LexiconAddComplexForm | factory.Create; .Add | high |
| Grammar/EnvironmentOperations.py | 182 | EnvironmentOperations.Delete | .Remove | high |
| Grammar/EnvironmentOperations.py | 260 | EnvironmentOperations.SetName | set_String | high |
| Grammar/GramCatOperations.py | 212 | GramCatOperations.Delete | .Remove | high |
| Grammar/GramCatOperations.py | 291 | GramCatOperations.SetName | set_String | high |
| Grammar/GramCatOperations.py | 544 | GramCatOperations.__DuplicateSubcategory | factory.Create; .Add | high |
| Grammar/InflectionFeatureOperations.py | 264 | InflectionFeatureOperations.InflectionClassDelete | .Remove | high |
| Grammar/InflectionFeatureOperations.py | 340 | InflectionFeatureOperations.InflectionClassSetName | set_String | high |
| Grammar/InflectionFeatureOperations.py | 415 | InflectionFeatureOperations.FeatureStructureCreate | factory.Create | high |
| Grammar/InflectionFeatureOperations.py | 449 | InflectionFeatureOperations.FeatureStructureDelete | prop assign (FeaturesOA) | high |
| Grammar/InflectionFeatureOperations.py | 1126 | InflectionFeatureOperations.FeatureDelete | .Remove | high |
| Grammar/InflectionFeatureOperations.py | 1416 | InflectionFeatureOperations._factory_create_attached | factory.Create | high |
| Grammar/InflectionFeatureOperations.py | 1433 | InflectionFeatureOperations._path_b_attach | .Add | high |
| Grammar/InflectionFeatureOperations.py | 1512 | InflectionFeatureOperations._CreateValueFromEntry | factory.Create; .Add | high |
| Grammar/InflectionFeatureOperations.py | 1766 | InflectionFeatureOperations.__OverlayCanonicalLabels | set_String | high |
| Grammar/MorphRuleOperations.py | 422 | MorphRuleOperations.Delete | .Remove | high |
| Grammar/MorphRuleOperations.py | 501 | MorphRuleOperations.SetName | set_String | high |
| Grammar/MorphRuleOperations.py | 566 | MorphRuleOperations.SetDescription | set_String | high |
| Grammar/MorphRuleOperations.py | 633 | MorphRuleOperations.SetStratum | prop assign (StratumRA) | high |
| Grammar/MorphRuleOperations.py | 830 | MorphRuleOperations.__DuplicateCompoundRule | factory.Create; .Insert; .Add | high |
| Grammar/MorphRuleOperations.py | 848 | MorphRuleOperations.__DuplicateAffixTemplate | factory.Create; .Insert; .Add | high |
| Grammar/NaturalClassOperations.py | 131 | NaturalClassOperations.__SetNameAndAbbreviation | set_String | high |
| Grammar/NaturalClassOperations.py | 306 | NaturalClassOperations.Delete | .Remove | high |
| Grammar/NaturalClassOperations.py | 499 | NaturalClassOperations.SetName | set_String | high |
| Grammar/NaturalClassOperations.py | 643 | NaturalClassOperations.AddPhoneme | .Add | high |
| Grammar/NaturalClassOperations.py | 702 | NaturalClassOperations.RemovePhoneme | .Remove | high |
| Grammar/POSOperations.py | 241 | POSOperations.Delete | .Remove | high |
| Grammar/POSOperations.py | 406 | POSOperations.SetName | set_String | high |
| Grammar/POSOperations.py | 477 | POSOperations.SetAbbreviation | set_String | high |
| Grammar/POSOperations.py | 632 | POSOperations.RemoveSubcategory | .Remove | high |
| Grammar/POSOperations.py | 956 | POSOperations.__DuplicateSubcategory | factory.Create; .Add | high |
| Grammar/POSOperations.py | 1016 | POSOperations._factory_create_attached | factory.Create | high |
| Grammar/POSOperations.py | 1037 | POSOperations._path_b_attach | .Add | high |
| Grammar/PhonFeatureOperations.py | 373 | PhonFeatureOperations.SetName | set_String | high |
| Grammar/PhonFeatureOperations.py | 390 | PhonFeatureOperations.SetAbbreviation | set_String | high |
| Grammar/PhonFeatureOperations.py | 409 | PhonFeatureOperations.SetDescription | set_String | high |
| Grammar/PhonFeatureOperations.py | 430 | PhonFeatureOperations.Delete | .Remove | high |
| Grammar/PhonFeatureOperations.py | 515 | PhonFeatureOperations.DeleteValue | .Remove | high |
| Grammar/PhonFeatureOperations.py | 785 | PhonFeatureOperations.__CreateValueWithGuid | factory.Create; .Add | high |
| Grammar/PhonFeatureOperations.py | 880 | PhonFeatureOperations._factory_create_attached | factory.Create | high |
| Grammar/PhonFeatureOperations.py | 897 | PhonFeatureOperations._path_b_attach | .Add | high |
| Grammar/PhonFeatureOperations.py | 968 | PhonFeatureOperations._CreateValueFromEntry | factory.Create; .Add | high |
| Grammar/PhonFeatureOperations.py | 1039 | PhonFeatureOperations.__OverlayCanonicalLabels | set_String | high |
| Grammar/PhonemeOperations.py | 235 | PhonemeOperations.Delete | .Remove | high |
| Grammar/PhonemeOperations.py | 512 | PhonemeOperations.SetRepresentation | set_String | high |
| Grammar/PhonemeOperations.py | 606 | PhonemeOperations.SetDescription | set_String | high |
| Grammar/PhonemeOperations.py | 820 | PhonemeOperations.RemoveCode | .Remove | high |
| Grammar/PhonemeOperations.py | 1055 | PhonemeOperations.SetBasicIPASymbol | set_String | high |
| Grammar/PhonemeOperations.py | 1440 | PhonemeOperations.__ApplyFeatures | factory.Create; prop assign (FeaturesOA); .Add; prop assign (FeatureRA) +more | high |
| Grammar/PhonologicalRuleOperations.py | 232 | PhonologicalRuleOperations.Delete | .Remove | high |
| Grammar/PhonologicalRuleOperations.py | 375 | PhonologicalRuleOperations.SetName | set_String | high |
| Grammar/PhonologicalRuleOperations.py | 445 | PhonologicalRuleOperations.SetDescription | set_String | high |
| Grammar/PhonologicalRuleOperations.py | 517 | PhonologicalRuleOperations.SetStratum | prop assign (StratumRA) | high |
| Grammar/PhonologicalRuleOperations.py | 754 | PhonologicalRuleOperations.DeleteConstraint | .Remove | high |
| Grammar/PhonologicalRuleOperations.py | 1012 | PhonologicalRuleOperations.__ClearSequence | .Remove | high |
| Grammar/PhonologicalRuleOperations.py | 1018 | PhonologicalRuleOperations.__CleanupSequenceContextMembers | .Remove | high |
| Grammar/PhonologicalRuleOperations.py | 1053 | PhonologicalRuleOperations.__WireContext | .Add; factory.Create | high |
| Grammar/PhonologicalRuleOperations.py | 1130 | PhonologicalRuleOperations.__BuildSimpleContext | factory.Create | high |
| Grammar/PhonologicalRuleOperations.py | 1175 | PhonologicalRuleOperations.__PopulateSimpleContext | prop assign (FeatureStructureRA); .Add | high |
| Grammar/StratumOperations.py | 215 | StratumOperations.Delete | .Remove | high |
| Lexicon/AllomorphOperations.py | 629 | AllomorphOperations.SetForm | set_String | high |
| Lexicon/AllomorphOperations.py | 902 | AllomorphOperations.SetMorphType | prop assign (MorphTypeRA) | high |
| Lexicon/AllomorphOperations.py | 982 | AllomorphOperations.AddPhoneEnv | .Add | high |
| Lexicon/AllomorphOperations.py | 1028 | AllomorphOperations.RemovePhoneEnv | .Remove | high |
| Lexicon/EtymologyOperations.py | 235 | EtymologyOperations.Delete | .Remove | high |
| Lexicon/EtymologyOperations.py | 663 | EtymologyOperations.SetSource | set_String | high |
| Lexicon/EtymologyOperations.py | 754 | EtymologyOperations.SetForm | set_String | high |
| Lexicon/EtymologyOperations.py | 841 | EtymologyOperations.SetGloss | set_String | high |
| Lexicon/EtymologyOperations.py | 926 | EtymologyOperations.SetComment | set_String | high |
| Lexicon/EtymologyOperations.py | 1034 | EtymologyOperations.SetBibliography | set_String | high |
| Lexicon/EtymologyOperations.py | 1194 | EtymologyOperations.SetLanguage | prop assign (LanguageRA) | high |
| Lexicon/ExampleOperations.py | 213 | ExampleOperations.Delete | .Remove | high |
| Lexicon/ExampleOperations.py | 697 | ExampleOperations.SetExample | set_String | high |
| Lexicon/ExampleOperations.py | 937 | ExampleOperations.RemoveTranslation | set_String | high |
| Lexicon/ExampleOperations.py | 1226 | ExampleOperations.RemoveMediaFile | .Remove | high |
| Lexicon/ExampleOperations.py | 1496 | ExampleOperations.SetLiteralTranslation | set_String | high |
| Lexicon/ExampleOperations.py | 1554 | ExampleOperations.AddDoNotPublishIn | .Add | high |
| Lexicon/ExampleOperations.py | 1584 | ExampleOperations.RemoveDoNotPublishIn | .Remove | high |
| Lexicon/LexEntryOperations.py | 249 | LexEntryOperations.Delete | .Delete | high |
| Lexicon/LexEntryOperations.py | 934 | LexEntryOperations.SetLexemeForm | set_String | high |
| Lexicon/LexEntryOperations.py | 1032 | LexEntryOperations.SetCitationForm | set_String | high |
| Lexicon/LexEntryOperations.py | 1478 | LexEntryOperations.SetMorphType | prop assign (MorphTypeRA) | high |
| Lexicon/LexEntryOperations.py | 2007 | LexEntryOperations.SetBibliography | set_String | high |
| Lexicon/LexEntryOperations.py | 2046 | LexEntryOperations.SetComment | set_String | high |
| Lexicon/LexEntryOperations.py | 2085 | LexEntryOperations.SetLiteralMeaning | set_String | high |
| Lexicon/LexEntryOperations.py | 2124 | LexEntryOperations.SetRestrictions | set_String | high |
| Lexicon/LexEntryOperations.py | 2163 | LexEntryOperations.SetSummaryDefinition | set_String | high |
| Lexicon/LexEntryOperations.py | 2278 | LexEntryOperations.AddDoNotPublishIn | .Add | high |
| Lexicon/LexEntryOperations.py | 2303 | LexEntryOperations.RemoveDoNotPublishIn | .Remove | high |
| Lexicon/LexEntryOperations.py | 2349 | LexEntryOperations.AddDoNotShowMainEntryIn | .Add | high |
| Lexicon/LexEntryOperations.py | 2374 | LexEntryOperations.RemoveDoNotShowMainEntryIn | .Remove | high |
| Lexicon/LexEntryOperations.py | 2929 | LexEntryOperations.__DeduplicateSensesInEntry | MergeObject | high |
| Lexicon/LexEntryOperations.py | 2989 | LexEntryOperations.__DeduplicatePronunciationsInEntry | .Remove | high |
| Lexicon/LexEntryOperations.py | 3052 | LexEntryOperations.__DeduplicateAllomorphsInEntry | .Remove | high |
| Lexicon/LexReferenceOperations.py | 283 | LexReferenceOperations.DeleteType | .Remove | high |
| Lexicon/LexReferenceOperations.py | 421 | LexReferenceOperations.SetTypeName | set_String | high |
| Lexicon/LexReferenceOperations.py | 508 | LexReferenceOperations.SetTypeReverseName | set_String | high |
| Lexicon/LexReferenceOperations.py | 780 | LexReferenceOperations.Delete | .Remove | high |
| Lexicon/LexReferenceOperations.py | 873 | LexReferenceOperations.AddTarget | .Add | high |
| Lexicon/LexReferenceOperations.py | 936 | LexReferenceOperations.RemoveTarget | .Remove | high |
| Lexicon/LexSenseOperations.py | 234 | LexSenseOperations.Delete | .Remove | high |
| Lexicon/LexSenseOperations.py | 374 | LexSenseOperations._deep_copy_sense_to | factory.Create; .Add | high |
| Lexicon/LexSenseOperations.py | 395 | LexSenseOperations.__copy_sense_content | prop assign (MorphoSyntaxAnalysisRA); prop assign (StatusRA); prop assign (SenseTypeRA); .Add +more | high |
| Lexicon/LexSenseOperations.py | 923 | LexSenseOperations.SetGloss | set_String | high |
| Lexicon/LexSenseOperations.py | 1012 | LexSenseOperations.SetDefinition | set_String | high |
| Lexicon/LexSenseOperations.py | 1533 | LexSenseOperations.SetGrammaticalInfo | prop assign (MorphoSyntaxAnalysisRA) | high |
| Lexicon/LexSenseOperations.py | 1610 | LexSenseOperations.AddSemanticDomain | .Add | high |
| Lexicon/LexSenseOperations.py | 1653 | LexSenseOperations.RemoveSemanticDomain | .Remove | high |
| Lexicon/LexSenseOperations.py | 2022 | LexSenseOperations.SetStatus | prop assign (StatusRA) | high |
| Lexicon/LexSenseOperations.py | 2099 | LexSenseOperations.SetSenseType | prop assign (SenseTypeRA) | high |
| Lexicon/LexSenseOperations.py | 2393 | LexSenseOperations.RemovePicture | .Remove | high |
| Lexicon/LexSenseOperations.py | 2551 | LexSenseOperations.SetCaption | set_String | high |
| Lexicon/LexSenseOperations.py | 2912 | LexSenseOperations.SetBibliography | set_String | high |
| Lexicon/LexSenseOperations.py | 2931 | LexSenseOperations.SetGeneralNote | set_String | high |
| Lexicon/LexSenseOperations.py | 2950 | LexSenseOperations.SetDiscourseNote | set_String | high |
| Lexicon/LexSenseOperations.py | 2969 | LexSenseOperations.SetEncyclopedicInfo | set_String | high |
| Lexicon/LexSenseOperations.py | 2988 | LexSenseOperations.SetGrammarNote | set_String | high |
| Lexicon/LexSenseOperations.py | 3007 | LexSenseOperations.SetPhonologyNote | set_String | high |
| Lexicon/LexSenseOperations.py | 3026 | LexSenseOperations.SetSemanticsNote | set_String | high |
| Lexicon/LexSenseOperations.py | 3045 | LexSenseOperations.SetSocioLinguisticsNote | set_String | high |
| Lexicon/LexSenseOperations.py | 3064 | LexSenseOperations.SetAnthroNote | set_String | high |
| Lexicon/LexSenseOperations.py | 3083 | LexSenseOperations.SetRestrictions | set_String | high |
| Lexicon/LexSenseOperations.py | 3225 | LexSenseOperations.AddUsageType | .Add | high |
| Lexicon/LexSenseOperations.py | 3246 | LexSenseOperations.RemoveUsageType | .Remove | high |
| Lexicon/LexSenseOperations.py | 3267 | LexSenseOperations.AddDomainType | .Add | high |
| Lexicon/LexSenseOperations.py | 3285 | LexSenseOperations.RemoveDomainType | .Remove | high |
| Lexicon/LexSenseOperations.py | 3306 | LexSenseOperations.AddAnthroCode | .Add | high |
| Lexicon/LexSenseOperations.py | 3324 | LexSenseOperations.RemoveAnthroCode | .Remove | high |
| Lexicon/LexSenseOperations.py | 3773 | LexSenseOperations.__DeduplicateExamplesInSense | .Remove | high |
| Lexicon/MSAOperations.py | 197 | MSAOperations.CreateDerivAff | prop assign (ToPartOfSpeechRA) | high |
| Lexicon/MSAOperations.py | 332 | MSAOperations.SetStemMsaPos | prop assign (PartOfSpeechRA) | high |
| Lexicon/MSAOperations.py | 426 | MSAOperations.ChangeAffixVariant | prop assign (FromPartOfSpeechRA); prop assign (ToPartOfSpeechRA); prop assign (MorphoSyntaxAnalysisRA); .Remove | high |
| Lexicon/PronunciationOperations.py | 220 | PronunciationOperations.Delete | .Remove | high |
| Lexicon/PronunciationOperations.py | 537 | PronunciationOperations.SetForm | set_String | high |
| Lexicon/PronunciationOperations.py | 658 | PronunciationOperations.AddMediaFile | .Add | high |
| Lexicon/PronunciationOperations.py | 721 | PronunciationOperations.RemoveMediaFile | .Remove | high |
| Lexicon/PronunciationOperations.py | 894 | PronunciationOperations.SetLocation | prop assign (LocationRA) | high |
| Lexicon/SemanticDomainOperations.py | 322 | SemanticDomainOperations.SetName | set_String | high |
| Lexicon/SemanticDomainOperations.py | 399 | SemanticDomainOperations.SetDescription | set_String | high |
| Lexicon/SemanticDomainOperations.py | 984 | SemanticDomainOperations.Delete | .Remove | high |
| Lexicon/VariantOperations.py | 438 | VariantOperations.Delete | .Remove | high |
| Lexicon/VariantOperations.py | 701 | VariantOperations.SetForm | set_String | high |
| Lexicon/VariantOperations.py | 898 | VariantOperations.AddComponentLexeme | .Add | high |
| Lexicon/VariantOperations.py | 951 | VariantOperations.RemoveComponentLexeme | .Remove | high |
| Lists/AgentOperations.py | 163 | AgentOperations.Delete | .Remove | high |
| Lists/OverlayOperations.py | 180 | OverlayOperations.SetVisible | prop assign (IsVisibleRA) | high |
| Lists/OverlayOperations.py | 314 | OverlayOperations.AddElement | .Add | high |
| Lists/OverlayOperations.py | 349 | OverlayOperations.RemoveElement | .Remove | high |
| Lists/PossibilityListOperations.py | 374 | PossibilityListOperations.SetListName | set_String | high |
| Lists/PossibilityListOperations.py | 538 | PossibilityListOperations.DeleteItem | .Remove | high |
| Lists/PossibilityListOperations.py | 778 | PossibilityListOperations.__DuplicateSubitemsRecursive | factory.Create; .Add | high |
| Lists/PossibilityListOperations.py | 897 | PossibilityListOperations.SetItemName | set_String | high |
| Lists/PossibilityListOperations.py | 968 | PossibilityListOperations.SetItemAbbreviation | set_String | high |
| Lists/PossibilityListOperations.py | 1040 | PossibilityListOperations.SetItemDescription | set_String | high |
| Lists/TranslationTypeOperations.py | 117 | TranslationTypeOperations.SetAbbreviation | set_String | high |
| Lists/possibility_item_base.py | 206 | PossibilityItemOperations.Delete | .Remove | needs-review |
| Lists/possibility_item_base.py | 336 | PossibilityItemOperations.SetName | set_String | needs-review |
| Lists/possibility_item_base.py | 380 | PossibilityItemOperations.SetDescription | set_String | needs-review |
| Notebook/AnthropologyOperations.py | 210 | AnthropologyOperations.Create | factory.Create; prop assign (AnthroListOA) | high |
| Notebook/AnthropologyOperations.py | 401 | AnthropologyOperations.Delete | .Remove | high |
| Notebook/AnthropologyOperations.py | 724 | AnthropologyOperations.SetName | set_String | high |
| Notebook/AnthropologyOperations.py | 816 | AnthropologyOperations.SetAbbreviation | set_String | high |
| Notebook/AnthropologyOperations.py | 902 | AnthropologyOperations.SetDescription | set_String | high |
| Notebook/AnthropologyOperations.py | 1086 | AnthropologyOperations.SetCategory | prop assign (CategoryRA) | high |
| Notebook/AnthropologyOperations.py | 1290 | AnthropologyOperations.AddText | .Add | high |
| Notebook/AnthropologyOperations.py | 1353 | AnthropologyOperations.RemoveText | .Remove | high |
| Notebook/AnthropologyOperations.py | 1554 | AnthropologyOperations.AddResearcher | .Add | high |
| Notebook/AnthropologyOperations.py | 1616 | AnthropologyOperations.RemoveResearcher | .Remove | high |
| Notebook/AnthropologyOperations.py | 1775 | AnthropologyOperations._DuplicateSubitemInto | factory.Create; .Add; prop assign (CategoryRA) | high |
| Notebook/DataNotebookOperations.py | 540 | DataNotebookOperations.SetTitle | set_String | high |
| Notebook/DataNotebookOperations.py | 636 | DataNotebookOperations.SetContent | set_String | high |
| Notebook/DataNotebookOperations.py | 1294 | DataNotebookOperations.AddResearcher | .Add | high |
| Notebook/DataNotebookOperations.py | 1347 | DataNotebookOperations.RemoveResearcher | .Remove | high |
| Notebook/DataNotebookOperations.py | 1433 | DataNotebookOperations.AddParticipant | .Add | high |
| Notebook/DataNotebookOperations.py | 1482 | DataNotebookOperations.RemoveParticipant | .Remove | high |
| Notebook/DataNotebookOperations.py | 1569 | DataNotebookOperations.AddLocation | .Add | high |
| Notebook/DataNotebookOperations.py | 1624 | DataNotebookOperations.RemoveLocation | .Remove | high |
| Notebook/DataNotebookOperations.py | 1711 | DataNotebookOperations.AddSource | .Add | high |
| Notebook/DataNotebookOperations.py | 1766 | DataNotebookOperations.RemoveSource | .Remove | high |
| Notebook/DataNotebookOperations.py | 1852 | DataNotebookOperations.LinkToText | .Add | high |
| Notebook/DataNotebookOperations.py | 1901 | DataNotebookOperations.UnlinkFromText | .Remove | high |
| Notebook/DataNotebookOperations.py | 1987 | DataNotebookOperations.AddMediaFile | .Add | high |
| Notebook/DataNotebookOperations.py | 2039 | DataNotebookOperations.RemoveMediaFile | .Remove | high |
| Notebook/DataNotebookOperations.py | 2431 | DataNotebookOperations.Duplicate | factory.Create; .Insert; .Add | high |
| Notebook/DataNotebookOperations.py | 2534 | DataNotebookOperations._DuplicateSubRecordInto | factory.Create; .Add | high |
| Notebook/LocationOperations.py | 1086 | LocationOperations.CreateSublocation | factory.Create; .Add; set_String | high |
| Notebook/LocationOperations.py | 1160 | LocationOperations.Duplicate | factory.Create; .Insert; .Add | high |
| Notebook/LocationOperations.py | 1269 | LocationOperations._DuplicateSublocationInto | factory.Create; .Add | high |
| Notebook/NoteOperations.py | 363 | NoteOperations._DuplicateReplyInto | factory.Create; .Add; prop assign (AnnotationTypeRA); prop assign (BeginObjectRA) | high |
| Notebook/NoteOperations.py | 607 | NoteOperations.SetNoteType | prop assign (AnnotationTypeRA) | high |
| Notebook/NoteOperations.py | 787 | NoteOperations.SetAuthor | set_String | high |
| Notebook/PersonOperations.py | 184 | PersonOperations.Delete | .Remove | high |
| Notebook/PersonOperations.py | 363 | PersonOperations.SetName | set_String | high |
| Notebook/PersonOperations.py | 449 | PersonOperations.SetGender | set_String | high |
| Notebook/PersonOperations.py | 606 | PersonOperations.SetEmail | set_String | high |
| Notebook/PersonOperations.py | 687 | PersonOperations.SetPhone | set_String | high |
| Notebook/PersonOperations.py | 769 | PersonOperations.SetAddress | set_String | high |
| Notebook/PersonOperations.py | 849 | PersonOperations.SetEducation | set_String | high |
| Notebook/PersonOperations.py | 929 | PersonOperations.AddPosition | .Add | high |
| Notebook/PersonOperations.py | 1319 | PersonOperations.AddResidence | .Add | high |
| Notebook/PersonOperations.py | 1398 | PersonOperations.AddLanguage | .Add | high |
| Notebook/PersonOperations.py | 1481 | PersonOperations.AddNote | set_String | high |
| Reversal/ReversalIndexEntryOperations.py | 203 | ReversalIndexEntryOperations.Delete | .Delete | high |
| Reversal/ReversalIndexEntryOperations.py | 373 | ReversalIndexEntryOperations.SetForm | set_String | high |
| Reversal/ReversalIndexEntryOperations.py | 454 | ReversalIndexEntryOperations.AddSense | .Add | high |
| Reversal/ReversalIndexEntryOperations.py | 492 | ReversalIndexEntryOperations.RemoveSense | .Remove | high |
| Reversal/ReversalIndexOperations.py | 180 | ReversalIndexOperations.Delete | .Delete | high |
| Reversal/ReversalIndexOperations.py | 344 | ReversalIndexOperations.SetName | set_String | high |
| Scripture/ScrAnnotationsOperations.py | 133 | ScrAnnotationsOperations.Delete | .Delete | high |
| Scripture/ScrBookOperations.py | 190 | ScrBookOperations.Delete | .Delete | high |
| Scripture/ScrBookOperations.py | 409 | ScrBookOperations.SetTitle | set_String | high |
| Scripture/ScrDraftOperations.py | 181 | ScrDraftOperations.Delete | .Delete | high |
| Scripture/ScrDraftOperations.py | 314 | ScrDraftOperations.SetDescription | set_String | high |
| Scripture/ScrNoteOperations.py | 202 | ScrNoteOperations.Delete | .Delete | high |
| Scripture/ScrSectionOperations.py | 80 | ScrSectionOperations.Create | factory.Create | high |
| Scripture/ScrSectionOperations.py | 140 | ScrSectionOperations.Delete | .Delete | high |
| Scripture/ScrTxtParaOperations.py | 162 | ScrTxtParaOperations.Delete | .Delete | high |
| Shared/FilterOperations.py | 833 | FilterOperations.ImportFilter | factory.Create | high |
| Shared/MediaOperations.py | 105 | MediaOperations.__GetOrCreateMediaFolder | factory.Create; .Add; set_String | high |
| Shared/MediaOperations.py | 186 | MediaOperations.Create | factory.Create; .Add; set_String | high |
| Shared/MediaOperations.py | 311 | MediaOperations.Duplicate | factory.Create | high |
| Shared/MediaOperations.py | 952 | MediaOperations.SetLabel | set_String | high |
| Shared/MediaOperations.py | 1280 | MediaOperations.CopyToProject | factory.Create | high |
| Shared/catalog_backed.py | 362 | CatalogBackedMixin.FixGuidsAgainstCatalog | MergeObject | needs-review |
| Shared/catalog_backed.py | 457 | CatalogBackedMixin._create_from_entry | factory.Create | needs-review |
| Shared/catalog_backed.py | 531 | CatalogBackedMixin._set_multistring | set_String | needs-review |
| System/AnnotationDefOperations.py | 414 | AnnotationDefOperations.SetName | set_String | high |
| System/AnnotationDefOperations.py | 495 | AnnotationDefOperations.SetHelpString | set_String | high |
| System/AnnotationDefOperations.py | 825 | AnnotationDefOperations.SetPrompt | set_String | high |
| System/AnnotationDefOperations.py | 1160 | AnnotationDefOperations._DuplicateSubDefInto | factory.Create; .Add | high |
| System/CheckOperations.py | 232 | CheckOperations.DeleteCheckType | .Remove | high |
| System/CheckOperations.py | 393 | CheckOperations.SetName | set_String | high |
| System/CheckOperations.py | 474 | CheckOperations.SetDescription | set_String | high |
| System/CheckOperations.py | 1175 | CheckOperations._GetOrCreateCheckList | factory.Create; set_String | high |
| System/CheckOperations.py | 1420 | CheckOperations._DuplicateSubCheckInto | factory.Create; .Add | high |
| System/CustomFieldOperations.py | 725 | CustomFieldOperations.ClearValue | set_String | high |
| System/ProjectSettingsOperations.py | 208 | ProjectSettingsOperations.SetDescription | set_String | high |
| TextsWords/DiscourseOperations.py | 357 | DiscourseOperations.DeleteChart | .Remove | high |
| TextsWords/DiscourseOperations.py | 447 | DiscourseOperations.SetChartName | set_String | high |
| TextsWords/DiscourseOperations.py | 707 | DiscourseOperations.DeleteRow | .Remove | high |
| TextsWords/DiscourseOperations.py | 807 | DiscourseOperations.SetCellContent | set_String | high |
| TextsWords/ParagraphOperations.py | 195 | ParagraphOperations.Delete | .Remove | high |
| TextsWords/SegmentOperations.py | 416 | SegmentOperations.SetFreeTranslation | set_String | high |
| TextsWords/SegmentOperations.py | 480 | SegmentOperations.SetLiteralTranslation | set_String | high |
| TextsWords/SegmentOperations.py | 633 | SegmentOperations.Delete | .Remove | high |
| TextsWords/SegmentOperations.py | 1083 | SegmentOperations.__MigrateTranslations | set_String; .MoveTo | high |
| TextsWords/TextOperations.py | 179 | TextOperations.Delete | .Remove | high |
| TextsWords/TextOperations.py | 562 | TextOperations.SetName | set_String | high |
| TextsWords/WfiAnalysisOperations.py | 411 | WfiAnalysisOperations.Delete | .Remove | high |
| TextsWords/WfiAnalysisOperations.py | 1329 | WfiAnalysisOperations.SetCategory | prop assign (CategoryRA) | high |
| TextsWords/WfiGlossOperations.py | 338 | WfiGlossOperations.Delete | .Remove | high |
| TextsWords/WfiGlossOperations.py | 498 | WfiGlossOperations.SetForm | set_String | high |
| TextsWords/WfiMorphBundleOperations.py | 189 | WfiMorphBundleOperations.Delete | .Remove | high |
| TextsWords/WfiMorphBundleOperations.py | 537 | WfiMorphBundleOperations.SetForm | set_String | high |
| TextsWords/WfiMorphBundleOperations.py | 730 | WfiMorphBundleOperations.SetSense | prop assign (SenseRA) | high |
| TextsWords/WfiMorphBundleOperations.py | 820 | WfiMorphBundleOperations.SetMorphType | prop assign (MorphRA) | high |
| TextsWords/WfiMorphBundleOperations.py | 909 | WfiMorphBundleOperations.SetMSA | prop assign (MsaRA) | high |
| TextsWords/WfiMorphBundleOperations.py | 1002 | WfiMorphBundleOperations.SetInflType | prop assign (InflTypeRA) | high |
| TextsWords/WfiMorphBundleOperations.py | 1096 | WfiMorphBundleOperations.SetInflectionClass | prop assign (InflClassRA) | high |
| TextsWords/WordformOperations.py | 178 | WordformOperations.Delete | .Delete | high |
| TextsWords/WordformOperations.py | 330 | WordformOperations.SetForm | set_String | high |

## Ambiguous cases

- `FLExProject.py:2772 FLExProject.SetAudioPath` - only `bldr.Clear()` / `bldr.Replace(...)` on a
  `TsStrBldr`; the resulting string is handed to a setter elsewhere. Excluded from the count.
- `FLExProject.py:3871/4092/4143/4192 LexiconAddEntry, LexiconAddAllomorph, LexiconAddPronunciation,
  LexiconAddVariantForm` - pure one-line delegations to `self.<Ops>.Create(...)`. Excluded.
- `Lexicon/MSAOperations.py:158/243/300 CreateStem, CreateInflAff, CreateUnclassifiedAffix` - mutate only
  a `SandboxGenericMSA` value object before handing it to `entry.FindOrCreateMSA`-style calls. Excluded,
  but the downstream call may itself write.
- `FLExProject.py` `DomainDataByFlid.SetString(...)` sites - raw cache-level writes, not property writes;
  marked needs-review.
- `BaseOperations.py`, `Lists/possibility_item_base.py`, `Shared/catalog_backed.py` - generic base-class
  helpers (`Sort`, `MoveUp`, `MoveDown`, `Delete`, ...) that mutate on behalf of many subclasses; all
  marked needs-review because the bracketing decision belongs to the subclass entry point.
