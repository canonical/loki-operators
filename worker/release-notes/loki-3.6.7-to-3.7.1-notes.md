# v3.6.7

Tag: v3.6.7
URL: https://github.com/grafana/loki/releases/tag/v3.6.7

## [3.6.7](https://github.com/grafana/loki/compare/v3.6.6...v3.6.7) (2026-02-23)


### Bug Fixes

* **alloc:** set a limit on preallocations (backport release-3.6.x) ([#20920](https://github.com/grafana/loki/issues/20920)) ([7e1daf3](https://github.com/grafana/loki/commit/7e1daf3a36f68639a5d06c1ac057a2fcbf0dce40))


================================================================================

# v3.6.8

Tag: v3.6.8
URL: https://github.com/grafana/loki/releases/tag/v3.6.8

## [3.6.8](https://github.com/grafana/loki/compare/v3.6.7...v3.6.8) (2026-03-25)


### Features

* Upgrade `go.opentelemetry.io/otel/sdk` from v1.38.0 to v1.40.0 ([#21115](https://github.com/grafana/loki/issues/21115)) ([d1ab148](https://github.com/grafana/loki/commit/d1ab148aa279e9e5263f699fa1b1a0e1eec14f1a))
* Upgrade Go to 1.25.8 (release-3.6.x) ([#21240](https://github.com/grafana/loki/issues/21240)) ([10d2666](https://github.com/grafana/loki/commit/10d266699420c158410e5af2521fff6ac4440d61))
* Upgrade Go used by querytee/promtail to 3.6 ([#21244](https://github.com/grafana/loki/issues/21244)) ([41a4e0c](https://github.com/grafana/loki/commit/41a4e0c702d35c52181ffb32d34bf8ad98cd7717))
* Use different debian version for fluent-bit ([#21247](https://github.com/grafana/loki/issues/21247)) ([138c391](https://github.com/grafana/loki/commit/138c391fd0237b8bf1eb9ecf9eb14d8ce04727c5))


### Bug Fixes

* **deps:** update module github.com/buger/jsonparser to v1.1.2 [security] (release-3.6.x) ([#21201](https://github.com/grafana/loki/issues/21201)) ([3185466](https://github.com/grafana/loki/commit/318546620179a198d9af21baab9c601f5cc367c1))
* **deps:** update module go.opentelemetry.io/otel/sdk to v1.40.0 [security] (release-3.6.x) ([#20887](https://github.com/grafana/loki/issues/20887)) ([d267ad3](https://github.com/grafana/loki/commit/d267ad368873ab3886519b975c86d76ded05741b))
* **deps:** update module google.golang.org/grpc to v1.79.3 [security] (release-3.6.x) ([#21193](https://github.com/grafana/loki/issues/21193)) ([87dff41](https://github.com/grafana/loki/commit/87dff4138d72c6616c47bcd2d46f04692af8d01f))


================================================================================

# v3.6.10

Tag: v3.6.10
URL: https://github.com/grafana/loki/releases/tag/v3.6.10

## [3.6.10](https://github.com/grafana/loki/compare/v3.6.8...v3.6.10) (2026-04-02)


### Bug Fixes

* Backporting 19989 into 3.6 ([#21356](https://github.com/grafana/loki/issues/21356)) ([0f56890](https://github.com/grafana/loki/commit/0f56890f0536200d1ebb22bcc3488d0e79d9285b))


================================================================================

# v3.7.0

Tag: v3.7.0
URL: https://github.com/grafana/loki/releases/tag/v3.7.0

## [3.7.0](https://github.com/grafana/loki/compare/v3.6.8...v3.7.0) (2026-03-26)


### ⚠ BREAKING CHANGES

* **engine:** Make scheduler aware of total compute capacity ([#19876](https://github.com/grafana/loki/issues/19876))
* parsed labels should not override structured metadata ([#19991](https://github.com/grafana/loki/issues/19991))
* **engine:** Share worker threads across all scheduler connections ([#20229](https://github.com/grafana/loki/issues/20229))

### Features

* ability to send query context for limit enforcement ([#19900](https://github.com/grafana/loki/issues/19900)) ([1a66d2d](https://github.com/grafana/loki/commit/1a66d2ddab11e7d0219040477ed2c0b95f87bfdb))
* add downscalePermittedFunc to check downscale is permitted ([#20171](https://github.com/grafana/loki/issues/20171)) ([c0c27b3](https://github.com/grafana/loki/commit/c0c27b3596d581f24f2c6b6ab101d99189f42ba0))
* add gauge to track in-flight bytes ([#20091](https://github.com/grafana/loki/issues/20091)) ([23ef8ec](https://github.com/grafana/loki/commit/23ef8eccce9b727509894b0056c65bd8083eea2e))
* add histogram loki_dataobj_consumer_flush_duration_seconds ([#20304](https://github.com/grafana/loki/issues/20304)) ([5a5e90e](https://github.com/grafana/loki/commit/5a5e90e9f70b1177b874fbf25986e1f74365e550))
* add loki health command ([#20313](https://github.com/grafana/loki/issues/20313)) ([ef69cfd](https://github.com/grafana/loki/commit/ef69cfd97cf1d5bd58758952cbc3eb48a99d060e))
* add metric to track flush failures ([#20399](https://github.com/grafana/loki/issues/20399)) ([ed4f27e](https://github.com/grafana/loki/commit/ed4f27ed60659cd234c06d8b6c90adcfc36f236e))
* Add new dataobj builder flush criteria ([#20323](https://github.com/grafana/loki/issues/20323)) ([498656b](https://github.com/grafana/loki/commit/498656bbe74076a1e54ccd27c587b0aac0a9a3a1))
* Add partition state to consumption lag metric ([#19912](https://github.com/grafana/loki/issues/19912)) ([91d4eb6](https://github.com/grafana/loki/commit/91d4eb6ce1288c921032b46bc338ce36a275da28))
* add prepare downscale handler ([#20007](https://github.com/grafana/loki/issues/20007)) ([677b2ec](https://github.com/grafana/loki/commit/677b2ecda1960d3c272dd41028879576737983bf))
* add processed records metric ([#20191](https://github.com/grafana/loki/issues/20191)) ([333da73](https://github.com/grafana/loki/commit/333da739c7bf17f6b5e08eed0caa91340a14934e))
* add race tolerance to query-tee ([#20228](https://github.com/grafana/loki/issues/20228)) ([014520a](https://github.com/grafana/loki/commit/014520a3d8535bc0dfd45c6146b6db7344df2f98))
* Add resolved policy to blocked and enforced label error ([#19826](https://github.com/grafana/loki/issues/19826)) ([48d13d1](https://github.com/grafana/loki/commit/48d13d15db864b524635823b432bbd45714714cd))
* add segmentation keys and resolver ([#19927](https://github.com/grafana/loki/issues/19927)) ([c853f2c](https://github.com/grafana/loki/commit/c853f2ced09b47f859a200718364df98def6e4c4))
* add support for cancelation to copy and sort ([#20370](https://github.com/grafana/loki/issues/20370)) ([6a8b879](https://github.com/grafana/loki/commit/6a8b879d8fe9bb51d1748ce18025c74d442bc379))
* Add support for storing chunk deletion markers in object storage instead of local disk ([#19689](https://github.com/grafana/loki/issues/19689)) ([856c11d](https://github.com/grafana/loki/commit/856c11dad209b05694626982230bbd7fa336e299))
* add support for UpdateRates RPC to distributors ([#19918](https://github.com/grafana/loki/issues/19918)) ([9018886](https://github.com/grafana/loki/commit/90188869a145bd640446b6ae7c123d03fc7f7a2a))
* Add UpdateRates RPC, update rates from the frontend, return no-op in the service ([#19894](https://github.com/grafana/loki/issues/19894)) ([e173cf4](https://github.com/grafana/loki/commit/e173cf4fb1fc54069b23e9959af6fc148a81b859))
* **canary:** Support passing arbitrary set of labels to use for the query ([#17008](https://github.com/grafana/loki/issues/17008)) ([993b3ae](https://github.com/grafana/loki/commit/993b3ae65dad2607d0d20459aac16de0ba2c1d5f))
* check partition state in parallel ([#19884](https://github.com/grafana/loki/issues/19884)) ([b8536aa](https://github.com/grafana/loki/commit/b8536aaa666271278a31362b96d34fcb1692d060))
* Client side index gateway shuffle sharding ([#20124](https://github.com/grafana/loki/issues/20124)) ([326c7d1](https://github.com/grafana/loki/commit/326c7d1ea0c5309568570d1128cc0e93d9479679))
* dataobj-consumer add processed bytes metric ([#20303](https://github.com/grafana/loki/issues/20303)) ([fba0c5d](https://github.com/grafana/loki/commit/fba0c5d8a60104ddf90d2ea239f434863dcad78b))
* decouple dataobj consumers from the reader service ([#20315](https://github.com/grafana/loki/issues/20315)) ([c3e909d](https://github.com/grafana/loki/commit/c3e909d538b438f30e9465ee68f3af7588d60037))
* disambiguate metadata for better scans ([#20245](https://github.com/grafana/loki/issues/20245)) ([66fd9d8](https://github.com/grafana/loki/commit/66fd9d8bdeac0e5e59da9fd2b8a3b070ea34f6bd))
* don't tee unsampled queries ([#20306](https://github.com/grafana/loki/issues/20306)) ([b975e48](https://github.com/grafana/loki/commit/b975e48d556fe6e1034f40370e6291870d6097d4))
* enable racing in the querytee ([#20156](https://github.com/grafana/loki/issues/20156)) ([23948c4](https://github.com/grafana/loki/commit/23948c40bda7a2b9398a2e74015b8e9dffc2aeef))
* Enable support for max, min, max_over_time, min_over_time for new engine ([#19841](https://github.com/grafana/loki/issues/19841)) ([b9a51f0](https://github.com/grafana/loki/commit/b9a51f0129a5c54b087dfad5ed0a2f784324a760))
* **engine:** add regexp parser support for log queries ([#20286](https://github.com/grafana/loki/issues/20286)) ([5663f9c](https://github.com/grafana/loki/commit/5663f9c26d54cc080da097c44c3195de4c210e1c))
* **engine:** delegate metastore queries to engine ([#20189](https://github.com/grafana/loki/issues/20189)) ([3a74fe7](https://github.com/grafana/loki/commit/3a74fe71fea86cd67d73bb6ac5bae487e8df9060))
* **engine:** implement strict and keepEmpty logfmt parsing ([#19668](https://github.com/grafana/loki/issues/19668)) ([01cab53](https://github.com/grafana/loki/commit/01cab53447b6b066680323658349540f69f9e669))
* **goldfish:** add endpoints for serving stored results ([#19640](https://github.com/grafana/loki/issues/19640)) ([e17ae2d](https://github.com/grafana/loki/commit/e17ae2d98f085ce037c86cb7508d65cc41658e41))
* **goldfish:** mv comparison_status to db, add stats endpoint ([#19698](https://github.com/grafana/loki/issues/19698)) ([c22e05c](https://github.com/grafana/loki/commit/c22e05c1f91ebcaf01dc9dc646d18251b8531837))
* Handle state change lock in prepare downscale  ([#20141](https://github.com/grafana/loki/issues/20141)) ([de092da](https://github.com/grafana/loki/commit/de092daf0ae6cc7656b0242348346aa1582f6656))
* **helm:** `nameOverride` now passed through helm tpl function. ([#19590](https://github.com/grafana/loki/issues/19590)) ([7f56fd2](https://github.com/grafana/loki/commit/7f56fd23df5f3fb02d3a40b6c421536e526cb221))
* **helm:** Add ability to toggle grpclb port for query frontend service ([#19609](https://github.com/grafana/loki/issues/19609)) ([9c4f022](https://github.com/grafana/loki/commit/9c4f0222b778d013ba20262cffcb93825bb3e6db))
* **helm:** Add startupProbe to distributor ([#20073](https://github.com/grafana/loki/issues/20073)) ([5b76589](https://github.com/grafana/loki/commit/5b76589e100e704f1f29f062c78ab52b619f9ede))
* **helm:** allow configuration of service trafficDistribution parameter ([#19558](https://github.com/grafana/loki/issues/19558)) ([55f95e3](https://github.com/grafana/loki/commit/55f95e3d1d425b495f0bbd0012665d3c60e4142a))
* **helm:** allow set topologySpreadConstraints on singleBinary ([#19534](https://github.com/grafana/loki/issues/19534)) ([265601f](https://github.com/grafana/loki/commit/265601f8310f5327aab14702437bc8cc3ebda04c))
* **helm:** make loki-canary readinessProbe configurable via values.yaml ([#19328](https://github.com/grafana/loki/issues/19328)) ([7231766](https://github.com/grafana/loki/commit/723176669ad3c0318adeeffa821bfd1ae36f88af))
* **helm:** use fsGroupChangePolicy=OnRootMismatch to speed up pod starts ([#13942](https://github.com/grafana/loki/issues/13942)) ([c7cec3a](https://github.com/grafana/loki/commit/c7cec3aa81924b58ddd755ce2f48e16252e80bfa))
* implement query splitting in the query-tee ([#20039](https://github.com/grafana/loki/issues/20039)) ([aab9e46](https://github.com/grafana/loki/commit/aab9e46bcfcc3248783613536a67d17edece40b9))
* **logcli:** Allow custom headers to be passed  ([#20231](https://github.com/grafana/loki/issues/20231)) ([c524203](https://github.com/grafana/loki/commit/c524203a6e37cf30f02f0c8eee0c9eef65e31c6b))
* **lokitool:** Add regex namespace filtering ([#20209](https://github.com/grafana/loki/issues/20209)) ([0c1561d](https://github.com/grafana/loki/commit/0c1561d15e9c9075cfb935efb0fc786664e68583))
* **metastore:** metastore DI ([#20253](https://github.com/grafana/loki/issues/20253)) ([9be17c7](https://github.com/grafana/loki/commit/9be17c7a42d55b593504a2b5084b5faa5d155d0c))
* **metastore:** shard sections queries over index files ([#20134](https://github.com/grafana/loki/issues/20134)) ([08e3c43](https://github.com/grafana/loki/commit/08e3c4385f7830d7097bc65e22aaa846c7f3dc89))
* **metastore:** use arrow for scanning and blooms ([#20234](https://github.com/grafana/loki/issues/20234)) ([e4ec844](https://github.com/grafana/loki/commit/e4ec8441d338d0772103b631afdeff8fe007b46d))
* **operator:** add option to disable ingress ([#19382](https://github.com/grafana/loki/issues/19382)) ([9dc71a6](https://github.com/grafana/loki/commit/9dc71a642569b64b6c21b23f23671b0f18f6285d))
* randomly distribute requests to the ingest-limits frontend ([#19840](https://github.com/grafana/loki/issues/19840)) ([1605a38](https://github.com/grafana/loki/commit/1605a387b765478fcb850e1e5a64dd5b924b751b))
* remove final flush ([#20360](https://github.com/grafana/loki/issues/20360)) ([3acb310](https://github.com/grafana/loki/commit/3acb3106bb303ca4a78068f66427c27e08a87bb1))
* shuffle shard on tenant rate limit ([#19990](https://github.com/grafana/loki/issues/19990)) ([3904c2b](https://github.com/grafana/loki/commit/3904c2b8f77252f6204dbec9ef4d995ad7b1ef68))
* **ui:** proxy analyze-labels to series with org id ([#19862](https://github.com/grafana/loki/issues/19862)) ([e268173](https://github.com/grafana/loki/commit/e2681737916ad20a534c502a82fed0bf2de2ccb4))
* write to dataobj partitions based on segmentation key ([#19946](https://github.com/grafana/loki/issues/19946)) ([3a24f5d](https://github.com/grafana/loki/commit/3a24f5d291c8398cd43346d8169e8a0646d8bf4f))


### Bug Fixes

* apply missing middlewares to query-tee ([#20184](https://github.com/grafana/loki/issues/20184)) ([b9c7ddd](https://github.com/grafana/loki/commit/b9c7dddac4017fc06197a1f464de83d717b4b3df))
* avoid recalculating the segmentation key hash twice ([#19961](https://github.com/grafana/loki/issues/19961)) ([8b78f79](https://github.com/grafana/loki/commit/8b78f7924d7414af116809912d76cfd4e71dcbda))
* bump helm deps, publish loki-helm-test w/ release ([#19939](https://github.com/grafana/loki/issues/19939)) ([7e4e34e](https://github.com/grafana/loki/commit/7e4e34e4c8da860f08db3c3d89eeb8d8d77d82dd))
* **cd:** add loki-image to needs ([#19870](https://github.com/grafana/loki/issues/19870)) ([a2c4ea6](https://github.com/grafana/loki/commit/a2c4ea66ac1aa8b0da077cdd91a20a171ee706c2))
* compactor file descriptor leak ([#20077](https://github.com/grafana/loki/issues/20077)) ([0c3dd8c](https://github.com/grafana/loki/commit/0c3dd8ce7efaebfc2d011b02c4dbd809e6955fec))
* **config:** migrate renovate config ([#19436](https://github.com/grafana/loki/issues/19436)) ([97745fe](https://github.com/grafana/loki/commit/97745fed6c384a695c4bf6d267d0b092c434ac64))
* **dataobj:** Flush into multiple index objects when ErrBuilderFull ([#19223](https://github.com/grafana/loki/issues/19223)) ([32dbef9](https://github.com/grafana/loki/commit/32dbef99b8ed8bf220eef569fd90acdaf624ca50))
* deadlock on shutdown ([#20384](https://github.com/grafana/loki/issues/20384)) ([272a278](https://github.com/grafana/loki/commit/272a2783802c4476d55ba4b8e89ebc02bb3f345e))
* **deps:** update dataobj-inspect transitive deps version ([#19813](https://github.com/grafana/loki/issues/19813)) ([5b212b7](https://github.com/grafana/loki/commit/5b212b7469945afa15a5a3a62ec69c63a09d2198))
* **deps:** update module cloud.google.com/go/bigtable to v1.41.0 (main) ([#20352](https://github.com/grafana/loki/issues/20352)) ([6102309](https://github.com/grafana/loki/commit/610230906ecd4f2a4c1a1ed5d39ce7ad294c4700))
* **deps:** update module cloud.google.com/go/pubsub to v1.50.1 (main) ([#18624](https://github.com/grafana/loki/issues/18624)) ([46038e4](https://github.com/grafana/loki/commit/46038e4b3d80250b9f4832fb09b735a21cf5680c))
* **deps:** update module cloud.google.com/go/pubsub to v2 (main) ([#19803](https://github.com/grafana/loki/issues/19803)) ([d47dde3](https://github.com/grafana/loki/commit/d47dde3e5aa66761d3bfc40d0bff86ae6e63eeb6))
* **deps:** update module cloud.google.com/go/storage to v1.57.1 (main) ([#19749](https://github.com/grafana/loki/issues/19749)) ([7ce0bf0](https://github.com/grafana/loki/commit/7ce0bf0581b8a4d669a46fc07353ed6507a33dba))
* **deps:** update module cloud.google.com/go/storage to v1.57.2 (main) ([#19893](https://github.com/grafana/loki/issues/19893)) ([e342642](https://github.com/grafana/loki/commit/e342642129982f2ef5f02060885d959b55391b30))
* **deps:** update module cloud.google.com/go/storage to v1.58.0 (main) ([#20159](https://github.com/grafana/loki/issues/20159)) ([e859215](https://github.com/grafana/loki/commit/e85921544a6ca9ad8ad42b20e29caa897905683c))
* **deps:** update module cloud.google.com/go/storage to v1.59.0 (main) ([#20407](https://github.com/grafana/loki/issues/20407)) ([5c71db6](https://github.com/grafana/loki/commit/5c71db648a5c32f809e216da6d7a48bc79f8c8f5))
* **deps:** update module github.com/alecthomas/chroma/v2 to v2.21.1 (main) ([#20353](https://github.com/grafana/loki/issues/20353)) ([6ef5f5c](https://github.com/grafana/loki/commit/6ef5f5c86d494dfb5fe2e04f4ef182bf1dbd4a28))
* **deps:** update module github.com/alecthomas/chroma/v2 to v2.22.0 (main) ([#20409](https://github.com/grafana/loki/issues/20409)) ([c64f044](https://github.com/grafana/loki/commit/c64f0443b599d47ae98936d1c1f6e2a352fc395b))
* **deps:** update module github.com/apache/arrow-go/v18 to v18.4.1 (main) ([#19750](https://github.com/grafana/loki/issues/19750)) ([d76b3bf](https://github.com/grafana/loki/commit/d76b3bf4951b3dfb3c67a793af1609f984c8df02))
* **deps:** update module github.com/apache/arrow-go/v18 to v18.5.0 (main) ([#20354](https://github.com/grafana/loki/issues/20354)) ([d0861a1](https://github.com/grafana/loki/commit/d0861a1f3475fd257d212f2f9c0548cfe0d635f6))
* **deps:** update module github.com/aws/aws-sdk-go-v2 to v1.39.6 (main) ([#19751](https://github.com/grafana/loki/issues/19751)) ([e2a5d59](https://github.com/grafana/loki/commit/e2a5d59757fb92bca3642d3e8c40845ab44c219f))
* **deps:** update module github.com/aws/aws-sdk-go-v2 to v1.40.1 (main) ([#20137](https://github.com/grafana/loki/issues/20137)) ([e106809](https://github.com/grafana/loki/commit/e10680982a83ea4d1e112553e2d43cc8ab818f65))
* **deps:** update module github.com/aws/aws-sdk-go-v2/config to v1.31.17 (main) ([#19773](https://github.com/grafana/loki/issues/19773)) ([06ada46](https://github.com/grafana/loki/commit/06ada4666600fc2206e5dcb67c7bcde1b13a771f))
* **deps:** update module github.com/aws/aws-sdk-go-v2/config to v1.31.18 (main) ([#19844](https://github.com/grafana/loki/issues/19844)) ([72c5d09](https://github.com/grafana/loki/commit/72c5d093b683300530d17a8551915284bf00d4d4))
* **deps:** update module github.com/aws/aws-sdk-go-v2/config to v1.31.20 (main) ([#19879](https://github.com/grafana/loki/issues/19879)) ([47560eb](https://github.com/grafana/loki/commit/47560ebacfe1f3e427eb7d6a9fb59606b965c65e))
* **deps:** update module github.com/aws/aws-sdk-go-v2/config to v1.32.0 (main) ([#19979](https://github.com/grafana/loki/issues/19979)) ([08e7418](https://github.com/grafana/loki/commit/08e7418d9273c08bb44201307faf5c343ba8f962))
* **deps:** update module github.com/aws/aws-sdk-go-v2/config to v1.32.1 (main) ([#20002](https://github.com/grafana/loki/issues/20002)) ([e37d83f](https://github.com/grafana/loki/commit/e37d83fab151ecbf225d4aa5615a2d0f51d3b60a))
* **deps:** update module github.com/aws/aws-sdk-go-v2/config to v1.32.2 (main) ([#20059](https://github.com/grafana/loki/issues/20059)) ([32f414c](https://github.com/grafana/loki/commit/32f414c0803f3db9068a7d01eeceebe8396e250c))
* **deps:** update module github.com/aws/aws-sdk-go-v2/config to v1.32.3 (main) ([#20138](https://github.com/grafana/loki/issues/20138)) ([0d7444a](https://github.com/grafana/loki/commit/0d7444a2b9a8e346919a7a128414598ffc45cdb9))
* **deps:** update module github.com/aws/aws-sdk-go-v2/config to v1.32.6 (main) ([#20338](https://github.com/grafana/loki/issues/20338)) ([6338096](https://github.com/grafana/loki/commit/633809601b3db12dc437b1432c2aa908f16e1b93))
* **deps:** update module github.com/aws/aws-sdk-go-v2/config to v1.32.7 (main) ([#20401](https://github.com/grafana/loki/issues/20401)) ([50ce71a](https://github.com/grafana/loki/commit/50ce71a5bfeb44ff7b8eff433930a6d23cac14b6))
* **deps:** update module github.com/aws/aws-sdk-go-v2/credentials to v1.18.21 (main) ([#19752](https://github.com/grafana/loki/issues/19752)) ([aebeb3c](https://github.com/grafana/loki/commit/aebeb3c31fb3c5fb529902938da3141ca8d92026))
* **deps:** update module github.com/aws/aws-sdk-go-v2/credentials to v1.18.24 (main) ([#19845](https://github.com/grafana/loki/issues/19845)) ([7e78f8c](https://github.com/grafana/loki/commit/7e78f8cb95296fc9b90ad28d6609d5b8bdcd1fba))
* **deps:** update module github.com/aws/aws-sdk-go-v2/credentials to v1.19.2 (main) ([#19980](https://github.com/grafana/loki/issues/19980)) ([c392438](https://github.com/grafana/loki/commit/c3924388586ab7122fd509bcd1bba9a3fd79df6b))
* **deps:** update module github.com/aws/aws-sdk-go-v2/credentials to v1.19.6 (main) ([#20339](https://github.com/grafana/loki/issues/20339)) ([3f29cae](https://github.com/grafana/loki/commit/3f29caee8a905341f1cc49e4904e23e418f627cc))
* **deps:** update module github.com/aws/aws-sdk-go-v2/credentials to v1.19.7 (main) ([#20402](https://github.com/grafana/loki/issues/20402)) ([f20228d](https://github.com/grafana/loki/commit/f20228dc547126239878028a0158d3bdebfd38d9))
* **deps:** update module github.com/aws/aws-sdk-go-v2/service/dynamodb to v1.52.4 (main) ([#19774](https://github.com/grafana/loki/issues/19774)) ([b5b8dd0](https://github.com/grafana/loki/commit/b5b8dd093565e00d9616f8795e037258c88ca861))
* **deps:** update module github.com/aws/aws-sdk-go-v2/service/dynamodb to v1.52.6 (main) ([#19846](https://github.com/grafana/loki/issues/19846)) ([0b25758](https://github.com/grafana/loki/commit/0b25758aad247eeaf885a79b8ac332fd57bcdbfd))
* **deps:** update module github.com/aws/aws-sdk-go-v2/service/dynamodb to v1.53.1 (main) ([#19981](https://github.com/grafana/loki/issues/19981)) ([c45abe6](https://github.com/grafana/loki/commit/c45abe62adb5837254b2ed5277fa4014f215e453))
* **deps:** update module github.com/aws/aws-sdk-go-v2/service/dynamodb to v1.53.2 (main) ([#20060](https://github.com/grafana/loki/issues/20060)) ([36079fa](https://github.com/grafana/loki/commit/36079faf4f62e0d074cfcc93f1f34404ad92d234))
* **deps:** update module github.com/aws/aws-sdk-go-v2/service/dynamodb to v1.53.3 (main) ([#20140](https://github.com/grafana/loki/issues/20140)) ([bfa8c38](https://github.com/grafana/loki/commit/bfa8c38e7eeca36486199b82f928dc9dc5bfb5b8))
* **deps:** update module github.com/aws/aws-sdk-go-v2/service/dynamodb to v1.53.5 (main) ([#20340](https://github.com/grafana/loki/issues/20340)) ([6d5d21e](https://github.com/grafana/loki/commit/6d5d21e46219b75a29ec8f3a747e6d3c3c303767))
* **deps:** update module github.com/aws/aws-sdk-go-v2/service/dynamodb to v1.53.6 (main) ([#20403](https://github.com/grafana/loki/issues/20403)) ([31a870c](https://github.com/grafana/loki/commit/31a870cc64615e163618c6afef4f828071d3f4cd))
* **deps:** update module github.com/aws/aws-sdk-go-v2/service/s3 to v1.88.4 (main) ([#19341](https://github.com/grafana/loki/issues/19341)) ([0b0faf1](https://github.com/grafana/loki/commit/0b0faf174bb3c1c24c6d706a261eda637f5e455e))
* **deps:** update module github.com/aws/aws-sdk-go-v2/service/s3 to v1.89.2 (main) ([#19775](https://github.com/grafana/loki/issues/19775)) ([0f37e57](https://github.com/grafana/loki/commit/0f37e574091c23431ca1e5711fc44082f13f2418))
* **deps:** update module github.com/aws/aws-sdk-go-v2/service/s3 to v1.90.0 (main) ([#19785](https://github.com/grafana/loki/issues/19785)) ([877a768](https://github.com/grafana/loki/commit/877a768f404722c0cbb09f25f595da8fd500e5dc))
* **deps:** update module github.com/aws/aws-sdk-go-v2/service/s3 to v1.90.2 (main) ([#19847](https://github.com/grafana/loki/issues/19847)) ([b50f3e3](https://github.com/grafana/loki/commit/b50f3e3e5898c6a5f5c83dfaf691350d6f7ce981))
* **deps:** update module github.com/aws/aws-sdk-go-v2/service/s3 to v1.92.0 (main) ([#19982](https://github.com/grafana/loki/issues/19982)) ([db87de8](https://github.com/grafana/loki/commit/db87de86f9941c81e78b1da99d929a8caf101dfb))
* **deps:** update module github.com/aws/aws-sdk-go-v2/service/s3 to v1.92.1 (main) ([#20061](https://github.com/grafana/loki/issues/20061)) ([a44b63c](https://github.com/grafana/loki/commit/a44b63cf8473de2793a1402b160aa831581d368f))
* **deps:** update module github.com/aws/aws-sdk-go-v2/service/s3 to v1.93.0 (main) ([#20142](https://github.com/grafana/loki/issues/20142)) ([87f3b59](https://github.com/grafana/loki/commit/87f3b590d59ff556d1f5a61bb21ae92ed8ac6cd0))
* **deps:** update module github.com/aws/aws-sdk-go-v2/service/s3 to v1.95.0 (main) ([#20355](https://github.com/grafana/loki/issues/20355)) ([d98d48b](https://github.com/grafana/loki/commit/d98d48bd94dd57f3fa0381ccf768f2c233a20c8e))
* **deps:** update module github.com/aws/aws-sdk-go-v2/service/s3 to v1.95.1 (main) ([#20406](https://github.com/grafana/loki/issues/20406)) ([c7c1411](https://github.com/grafana/loki/commit/c7c14114f44cfc77cb8f8635a5b7340ce3a9e329))
* **deps:** update module github.com/aws/smithy-go to v1.23.2 (main) ([#19753](https://github.com/grafana/loki/issues/19753)) ([61b8049](https://github.com/grafana/loki/commit/61b8049bd00299e67b88269b529de521a1c7de53))
* **deps:** update module github.com/aws/smithy-go to v1.24.0 (main) ([#20117](https://github.com/grafana/loki/issues/20117)) ([b0efa70](https://github.com/grafana/loki/commit/b0efa70f4b1707cda25bb4324d02af71fdc23e77))
* **deps:** update module github.com/axiomhq/hyperloglog to v0.2.6 (main) ([#20341](https://github.com/grafana/loki/issues/20341)) ([4469f82](https://github.com/grafana/loki/commit/4469f826d2df54486b6c51a1a3e7b899c5d5a1d6))
* **deps:** update module github.com/baidubce/bce-sdk-go to v0.9.251 (main) ([#19754](https://github.com/grafana/loki/issues/19754)) ([7257d31](https://github.com/grafana/loki/commit/7257d3116afa939fa0e732d600bbe14cab755224))
* **deps:** update module github.com/baidubce/bce-sdk-go to v0.9.252 (main) ([#19972](https://github.com/grafana/loki/issues/19972)) ([c4c5ed7](https://github.com/grafana/loki/commit/c4c5ed734fd663b2168407a5926ccf2bc59cf448))
* **deps:** update module github.com/baidubce/bce-sdk-go to v0.9.253 (main) ([#20125](https://github.com/grafana/loki/issues/20125)) ([d28862b](https://github.com/grafana/loki/commit/d28862b53b1f1e73e835bbf9abb1725c46f49096))
* **deps:** update module github.com/baidubce/bce-sdk-go to v0.9.256 (main) ([#20342](https://github.com/grafana/loki/issues/20342)) ([69e6254](https://github.com/grafana/loki/commit/69e625405628ac25b7fabe07a809df0d4e6b73e1))
* **deps:** update module github.com/bits-and-blooms/bloom/v3 to v3.7.1 (main) ([#19755](https://github.com/grafana/loki/issues/19755)) ([af47e1f](https://github.com/grafana/loki/commit/af47e1f4feabb62824376e51d1ae80a4a28c2d89))
* **deps:** update module github.com/bmatcuk/doublestar/v4 to v4.9.2 (main) ([#20418](https://github.com/grafana/loki/issues/20418)) ([078dc94](https://github.com/grafana/loki/commit/078dc945551d4ba4f918653c4c758f4fc6525931))
* **deps:** update module github.com/coder/quartz to v0.3.0 (main) ([#19786](https://github.com/grafana/loki/issues/19786)) ([6f784f9](https://github.com/grafana/loki/commit/6f784f99d4ca208835a488874e9d12dea5020ad5))
* **deps:** update module github.com/docker/docker to v28.5.2+incompatible (main) ([#19756](https://github.com/grafana/loki/issues/19756)) ([1007ee4](https://github.com/grafana/loki/commit/1007ee4a89c439791fb1b1a7b5e155ab91e8b6d2))
* **deps:** update module github.com/gocql/gocql to v2 (main) ([#19794](https://github.com/grafana/loki/issues/19794)) ([898b6d2](https://github.com/grafana/loki/commit/898b6d20374015dd5cf12571fae91393c6e22c9b))
* **deps:** update module github.com/google/renameio/v2 to v2.0.1 (main) ([#19935](https://github.com/grafana/loki/issues/19935)) ([f943b39](https://github.com/grafana/loki/commit/f943b390f3df26e89f4137d27d8558a72fa9e3d3))
* **deps:** update module github.com/google/renameio/v2 to v2.0.2 (main) ([#20411](https://github.com/grafana/loki/issues/20411)) ([cc43074](https://github.com/grafana/loki/commit/cc4307424575386914b6c40bc605155710f46e06))
* **deps:** update module github.com/grafana/loki/v3 to v3.5.8 (main) ([#19757](https://github.com/grafana/loki/issues/19757)) ([7c0921c](https://github.com/grafana/loki/commit/7c0921c8442435f71fd1850886ae6c8d93492b1b))
* **deps:** update module github.com/grafana/loki/v3 to v3.6.0 (main) ([#19943](https://github.com/grafana/loki/issues/19943)) ([2d00410](https://github.com/grafana/loki/commit/2d00410c14c96f1be4f0ee2b7dd6eb9c58fe7797))
* **deps:** update module github.com/grafana/loki/v3 to v3.6.1 (main) ([#19993](https://github.com/grafana/loki/issues/19993)) ([116aa1c](https://github.com/grafana/loki/commit/116aa1c4e2c5e46c57c75125fdc18c907df911f7))
* **deps:** update module github.com/grafana/loki/v3 to v3.6.2 (main) ([#20057](https://github.com/grafana/loki/issues/20057)) ([b4f6138](https://github.com/grafana/loki/commit/b4f6138f1830260f3dea85114a19184b2ea9bce1))
* **deps:** update module github.com/grafana/loki/v3 to v3.6.3 (main) ([#20343](https://github.com/grafana/loki/issues/20343)) ([d1ae7a1](https://github.com/grafana/loki/commit/d1ae7a1ba35e9775dcbf58b8081e214157d1a16d))
* **deps:** update module github.com/grpc-ecosystem/go-grpc-middleware/v2 to v2.3.3 (main) ([#19758](https://github.com/grafana/loki/issues/19758)) ([8133da9](https://github.com/grafana/loki/commit/8133da968d8e8eb4b21d254368a40c01acd68ccb))
* **deps:** update module github.com/hashicorp/consul/api to v1.33.0 (main) ([#19788](https://github.com/grafana/loki/issues/19788)) ([e417259](https://github.com/grafana/loki/commit/e417259980d7edf2f75eefeac94efd351421d99e))
* **deps:** update module github.com/ibm/go-sdk-core/v5 to v5.21.1 (main) ([#19950](https://github.com/grafana/loki/issues/19950)) ([cd408bc](https://github.com/grafana/loki/commit/cd408bc59bf9fb1a4072bc6846ee9b540dbd1c29))
* **deps:** update module github.com/ibm/go-sdk-core/v5 to v5.21.2 (main) ([#19988](https://github.com/grafana/loki/issues/19988)) ([d8ab970](https://github.com/grafana/loki/commit/d8ab970b1cf5bfb2864e6c92b2de05bbd66feb0e))
* **deps:** update module github.com/ibm/ibm-cos-sdk-go to v1.12.4 (main) ([#20146](https://github.com/grafana/loki/issues/20146)) ([a80774b](https://github.com/grafana/loki/commit/a80774b2b1fb6b41509c04a539a904b4463d84fb))
* **deps:** update module github.com/ibm/ibm-cos-sdk-go to v1.13.0 (main) ([#20364](https://github.com/grafana/loki/issues/20364)) ([52d1d8d](https://github.com/grafana/loki/commit/52d1d8d96669075d6685b64508766fb4549cf009))
* **deps:** update module github.com/ibm/sarama to v1.46.3 (main) ([#19760](https://github.com/grafana/loki/issues/19760)) ([4a19787](https://github.com/grafana/loki/commit/4a19787dff6fcca74a380b686dc58882f7195a3a))
* **deps:** update module github.com/influxdata/telegraf to v1.36.3 (main) ([#19796](https://github.com/grafana/loki/issues/19796)) ([4911c98](https://github.com/grafana/loki/commit/4911c989e636741f84d083e690fcba2a89b33014))
* **deps:** update module github.com/influxdata/telegraf to v1.36.4 (main) ([#19938](https://github.com/grafana/loki/issues/19938)) ([d6147d8](https://github.com/grafana/loki/commit/d6147d81a191f958d78445b6d8f81314d63ba9a0))
* **deps:** update module github.com/influxdata/telegraf to v1.37.0 (main) ([#20356](https://github.com/grafana/loki/issues/20356)) ([dc1e0ae](https://github.com/grafana/loki/commit/dc1e0aefcb004662b70d704ea8b11e7df26fa8e9))
* **deps:** update module github.com/klauspost/compress to v1.18.1 (main) ([#19761](https://github.com/grafana/loki/issues/19761)) ([c5e7293](https://github.com/grafana/loki/commit/c5e72930974eb9f7fc88b042d1d354b8a36affd9))
* **deps:** update module github.com/klauspost/compress to v1.18.2 (main) ([#20108](https://github.com/grafana/loki/issues/20108)) ([f4f2b2a](https://github.com/grafana/loki/commit/f4f2b2a718b2d591adb99b358430ad905c3fa4ee))
* **deps:** update module github.com/leodido/go-syslog/v4 to v4.3.0 (main) ([#19416](https://github.com/grafana/loki/issues/19416)) ([036387b](https://github.com/grafana/loki/commit/036387b297cb99c28f1aaa1c6751b004b167edba))
* **deps:** update module github.com/minio/minio-go/v7 to v7.0.97 (main) ([#19762](https://github.com/grafana/loki/issues/19762)) ([ee2b424](https://github.com/grafana/loki/commit/ee2b42413b731de64f991963e4986f44c86e9c4c))
* **deps:** update module github.com/minio/minio-go/v7 to v7.0.98 (main) ([#20436](https://github.com/grafana/loki/issues/20436)) ([cf89342](https://github.com/grafana/loki/commit/cf893421f2fe51853331dc318843dde4b0969807))
* **deps:** update module github.com/ncw/swift/v2 to v2.0.5 (main) ([#19764](https://github.com/grafana/loki/issues/19764)) ([fa5e144](https://github.com/grafana/loki/commit/fa5e144b42a5d0e4347a366213fd491ec808603e))
* **deps:** update module github.com/oschwald/geoip2-golang to v2 (main) ([#19799](https://github.com/grafana/loki/issues/19799)) ([33eeab6](https://github.com/grafana/loki/commit/33eeab62c144a78cb0511c8d5321591ce5f0d03e))
* **deps:** update module github.com/oschwald/geoip2-golang/v2 to v2.0.1 (main) ([#20065](https://github.com/grafana/loki/issues/20065)) ([ac5df60](https://github.com/grafana/loki/commit/ac5df60537b8c5a41ac654c400be89a174bed56a))
* **deps:** update module github.com/oschwald/geoip2-golang/v2 to v2.1.0 (main) ([#20357](https://github.com/grafana/loki/issues/20357)) ([8853d71](https://github.com/grafana/loki/commit/8853d710d4582b5591c0bc7fa192a3e228ee0a9a))
* **deps:** update module github.com/parquet-go/parquet-go to v0.26.0 (main) ([#20170](https://github.com/grafana/loki/issues/20170)) ([9ffe31e](https://github.com/grafana/loki/commit/9ffe31e6e423741eb775fb5d334e206352e1facb))
* **deps:** update module github.com/parquet-go/parquet-go to v0.26.4 (main) ([#20344](https://github.com/grafana/loki/issues/20344)) ([caa21ae](https://github.com/grafana/loki/commit/caa21ae58529166707b7c892097c1c8c55eac3c6))
* **deps:** update module github.com/parquet-go/parquet-go to v0.27.0 (main) ([#20426](https://github.com/grafana/loki/issues/20426)) ([a283eac](https://github.com/grafana/loki/commit/a283eac267662b5239430cfcb70893460ec84657))
* **deps:** update module github.com/prometheus/alertmanager to v0.29.0 (main) ([#19797](https://github.com/grafana/loki/issues/19797)) ([5ec7ddc](https://github.com/grafana/loki/commit/5ec7ddca47bb63413f9922065549a30565b85043))
* **deps:** update module github.com/prometheus/alertmanager to v0.30.0 (main) ([#20358](https://github.com/grafana/loki/issues/20358)) ([f53a609](https://github.com/grafana/loki/commit/f53a609be4c9c32f4ad03a4a61daa5e0b525f989))
* **deps:** update module github.com/prometheus/client_golang to v1.23.2 (main) ([#19763](https://github.com/grafana/loki/issues/19763)) ([8317f7e](https://github.com/grafana/loki/commit/8317f7e4629be6bc8f40579f00c2151fb126fb4c))
* **deps:** update module github.com/prometheus/common to v0.67.3 (main) ([#19906](https://github.com/grafana/loki/issues/19906)) ([aafc579](https://github.com/grafana/loki/commit/aafc5792e23ca987b55406a3467a9575e5c15a73))
* **deps:** update module github.com/prometheus/common to v0.67.4 (main) ([#19994](https://github.com/grafana/loki/issues/19994)) ([ccc6d73](https://github.com/grafana/loki/commit/ccc6d738b52df2defd012f76bbe1d025f0782dce))
* **deps:** update module github.com/prometheus/common to v0.67.5 (main) ([#20363](https://github.com/grafana/loki/issues/20363)) ([aaacbf4](https://github.com/grafana/loki/commit/aaacbf4edaa2fd657cd1376fcb3fb53a2d029757))
* **deps:** update module github.com/prometheus/prometheus to v0.307.3 (main) ([#19800](https://github.com/grafana/loki/issues/19800)) ([7912a67](https://github.com/grafana/loki/commit/7912a67efceee2afc48b61f1ee66d01bc12f7fbd))
* **deps:** update module github.com/prometheus/prometheus to v0.308.0 (main) ([#20131](https://github.com/grafana/loki/issues/20131)) ([0aac50b](https://github.com/grafana/loki/commit/0aac50bffb49f28d13399d828d46e4cdef7e65fa))
* **deps:** update module github.com/prometheus/prometheus to v0.308.1 (main) ([#20346](https://github.com/grafana/loki/issues/20346)) ([393d4cd](https://github.com/grafana/loki/commit/393d4cd0fb9da162492e0ad8c197b701b8202a81))
* **deps:** update module github.com/prometheus/prometheus to v0.309.1 (main) ([#20388](https://github.com/grafana/loki/issues/20388)) ([bf79bcf](https://github.com/grafana/loki/commit/bf79bcff061caecd0a2d6828c1b8ec31990f2a9c))
* **deps:** update module github.com/prometheus/sigv4 to v0.3.0 (main) ([#19801](https://github.com/grafana/loki/issues/19801)) ([adaf758](https://github.com/grafana/loki/commit/adaf758cbe90d1a2b3416c4c79d32981ccb56201))
* **deps:** update module github.com/prometheus/sigv4 to v0.4.0 (main) ([#20386](https://github.com/grafana/loki/issues/20386)) ([2f80526](https://github.com/grafana/loki/commit/2f80526f19a036513d9849876717c17678bc9ff6))
* **deps:** update module github.com/redis/go-redis/v9 to v9.16.0 (main) ([#19819](https://github.com/grafana/loki/issues/19819)) ([ea00c15](https://github.com/grafana/loki/commit/ea00c1556fdd150c9e0e7fea2c71428abd01bbc5))
* **deps:** update module github.com/redis/go-redis/v9 to v9.17.0 (main) ([#19977](https://github.com/grafana/loki/issues/19977)) ([723ff2d](https://github.com/grafana/loki/commit/723ff2ded9301d5781f10d166f6bcaf88adee61f))
* **deps:** update module github.com/redis/go-redis/v9 to v9.17.1 (main) ([#20063](https://github.com/grafana/loki/issues/20063)) ([69fdd6c](https://github.com/grafana/loki/commit/69fdd6cc9c41b28b189bf41b7f704c9210a2d829))
* **deps:** update module github.com/redis/go-redis/v9 to v9.17.2 (main) ([#20116](https://github.com/grafana/loki/issues/20116)) ([434a929](https://github.com/grafana/loki/commit/434a9295a57d0469826e9f8aa252a2bc1a1ebaaa))
* **deps:** update module github.com/schollz/progressbar/v3 to v3.19.0 (main) ([#20365](https://github.com/grafana/loki/issues/20365)) ([0b238bc](https://github.com/grafana/loki/commit/0b238bccea4babd97b3393de9ac0380e7c65a66c))
* **deps:** update module github.com/shirou/gopsutil/v4 to v4.25.10 (main) ([#19765](https://github.com/grafana/loki/issues/19765)) ([363dd11](https://github.com/grafana/loki/commit/363dd11ef18ff9f628309bfc2fc91cca8e3c5b52))
* **deps:** update module github.com/shirou/gopsutil/v4 to v4.25.11 (main) ([#20066](https://github.com/grafana/loki/issues/20066)) ([76cc947](https://github.com/grafana/loki/commit/76cc9479518a4dd4fa713349ce4bd3166bfbf067))
* **deps:** update module github.com/shirou/gopsutil/v4 to v4.25.12 (main) ([#20347](https://github.com/grafana/loki/issues/20347)) ([0740eb8](https://github.com/grafana/loki/commit/0740eb8a56b1e57000eb4e6862ee75d3c3f15b0f))
* **deps:** update module github.com/sirupsen/logrus to v1.9.4 (main) ([#20447](https://github.com/grafana/loki/issues/20447)) ([35c8df7](https://github.com/grafana/loki/commit/35c8df7705afd31f8d735533a9d15175d273a616))
* **deps:** update module github.com/sony/gobreaker/v2 to v2.4.0 (main) ([#20366](https://github.com/grafana/loki/issues/20366)) ([090ffd5](https://github.com/grafana/loki/commit/090ffd517252ea39a96fac037afe85119b9a9bd0))
* **deps:** update module github.com/tjhop/slog-gokit to v0.1.5 (main) ([#19808](https://github.com/grafana/loki/issues/19808)) ([615413e](https://github.com/grafana/loki/commit/615413e269f7ed4b52fbd752e4cde29e773d454d))
* **deps:** update module github.com/twmb/franz-go to v1.20.2 (main) ([#19789](https://github.com/grafana/loki/issues/19789)) ([5264a7e](https://github.com/grafana/loki/commit/5264a7eb237536787511bed8e559e90a64c91e67))
* **deps:** update module github.com/twmb/franz-go to v1.20.3 (main) ([#19812](https://github.com/grafana/loki/issues/19812)) ([ceb7c84](https://github.com/grafana/loki/commit/ceb7c8493c54fc8ef30ec04cd60d51972dfd9e14))
* **deps:** update module github.com/twmb/franz-go to v1.20.4 (main) ([#19902](https://github.com/grafana/loki/issues/19902)) ([57b8346](https://github.com/grafana/loki/commit/57b8346452a8a9118cb9b142c69a40ae761852c6))
* **deps:** update module github.com/twmb/franz-go to v1.20.5 (main) ([#20038](https://github.com/grafana/loki/issues/20038)) ([c9a30b1](https://github.com/grafana/loki/commit/c9a30b1e54a03733f9dbef21185ae90e0c423daf))
* **deps:** update module github.com/twmb/franz-go to v1.20.6 (main) ([#20348](https://github.com/grafana/loki/issues/20348)) ([5ee4fee](https://github.com/grafana/loki/commit/5ee4fee4bc66e179dd8717d09699353932d119e7))
* **deps:** update module github.com/twmb/franz-go/pkg/kadm to v1.17.1 (main) ([#19790](https://github.com/grafana/loki/issues/19790)) ([1dad0be](https://github.com/grafana/loki/commit/1dad0be6b7ba439a2be9a64562b3762e495d6950))
* **deps:** update module github.com/twmb/franz-go/pkg/kmsg to v1.12.0 (main) ([#19791](https://github.com/grafana/loki/issues/19791)) ([f28c247](https://github.com/grafana/loki/commit/f28c247cb47dca402b8465e9ff5373d288df17bc))
* **deps:** update module github.com/workiva/go-datastructures to v1.1.7 (main) ([#19766](https://github.com/grafana/loki/issues/19766)) ([f5e0683](https://github.com/grafana/loki/commit/f5e0683986cec6d5edd643626c2dcbb4e894a65e))
* **deps:** update module github.com/xdg-go/scram to v1.2.0 (main) ([#20046](https://github.com/grafana/loki/issues/20046)) ([9e52320](https://github.com/grafana/loki/commit/9e523207b8c3afcdb810ca4f4d47b43887235346))
* **deps:** update module go.opentelemetry.io/collector/pdata to v1.46.0 (main) ([#19802](https://github.com/grafana/loki/issues/19802)) ([87b558c](https://github.com/grafana/loki/commit/87b558cda7e62145eb857dada7b07fc725aaba6e))
* **deps:** update module go.opentelemetry.io/collector/pdata to v1.47.0 (main) ([#20112](https://github.com/grafana/loki/issues/20112)) ([e5bf3bc](https://github.com/grafana/loki/commit/e5bf3bc0c93e970c43c625396049d80b07bcdd51))
* **deps:** update module go.opentelemetry.io/collector/pdata to v1.49.0 (main) ([#20371](https://github.com/grafana/loki/issues/20371)) ([7d759f2](https://github.com/grafana/loki/commit/7d759f215d1167b46470fa40a9812d3d3a53126c))
* **deps:** update module go.opentelemetry.io/contrib/instrumentation/google.golang.org/grpc/otelgrpc to v0.64.0 (main) ([#20372](https://github.com/grafana/loki/issues/20372)) ([9da1b1b](https://github.com/grafana/loki/commit/9da1b1bcd5643148e0d749b4d780606712d0f6b2))
* **deps:** update module go.opentelemetry.io/contrib/instrumentation/net/http/httptrace/otelhttptrace to v0.64.0 (main) ([#20373](https://github.com/grafana/loki/issues/20373)) ([719635a](https://github.com/grafana/loki/commit/719635ad80c31a005ab6809cf7cab947611e20c7))
* **deps:** update module go.opentelemetry.io/contrib/instrumentation/net/http/otelhttp to v0.64.0 (main) ([#20374](https://github.com/grafana/loki/issues/20374)) ([f1b3e1b](https://github.com/grafana/loki/commit/f1b3e1bf67ed296edf49ed8c30fed800be147d9b))
* **deps:** update module go.opentelemetry.io/otel/sdk to v1.39.0 (main) ([#20376](https://github.com/grafana/loki/issues/20376)) ([95b82d6](https://github.com/grafana/loki/commit/95b82d66b701afc8c9473a68dccd27251a9b824c))
* **deps:** update module golang.org/x/crypto to v0.44.0 (main) ([#19776](https://github.com/grafana/loki/issues/19776)) ([c85c67a](https://github.com/grafana/loki/commit/c85c67ac77f900655f2bbe41b6793eb4e05c7f7f))
* **deps:** update module golang.org/x/net to v0.46.0 (main) ([#19777](https://github.com/grafana/loki/issues/19777)) ([27740ca](https://github.com/grafana/loki/commit/27740ca5b99351fb3d28a96d4069481fed398775))
* **deps:** update module golang.org/x/net to v0.47.0 (main) ([#19850](https://github.com/grafana/loki/issues/19850)) ([5c422a6](https://github.com/grafana/loki/commit/5c422a6b9010fb2bf05c7f56e955cc0acf5a429b))
* **deps:** update module golang.org/x/oauth2 to v0.33.0 (main) ([#19778](https://github.com/grafana/loki/issues/19778)) ([1954778](https://github.com/grafana/loki/commit/1954778b45e0d02dde421dbc944ba65674b9bf40))
* **deps:** update module golang.org/x/oauth2 to v0.34.0 (main) ([#20160](https://github.com/grafana/loki/issues/20160)) ([ebf7b93](https://github.com/grafana/loki/commit/ebf7b93c67139b5d329dd3c951aedc900824513b))
* **deps:** update module golang.org/x/sync to v0.18.0 (main) ([#19779](https://github.com/grafana/loki/issues/19779)) ([8772fad](https://github.com/grafana/loki/commit/8772fad52e63c483383ef0d536e3d51293f5760c))
* **deps:** update module golang.org/x/sync to v0.19.0 (main) ([#20161](https://github.com/grafana/loki/issues/20161)) ([817b9d8](https://github.com/grafana/loki/commit/817b9d8c9c43aae0d4f1f54a13889a1a1d18e7c6))
* **deps:** update module golang.org/x/sys to v0.38.0 (main) ([#19780](https://github.com/grafana/loki/issues/19780)) ([92a8518](https://github.com/grafana/loki/commit/92a85189d57bc5acb7f85279c139a4fae6aba180))
* **deps:** update module golang.org/x/sys to v0.39.0 (main) ([#20162](https://github.com/grafana/loki/issues/20162)) ([f0a9bae](https://github.com/grafana/loki/commit/f0a9bae3b30ddecb18f4f89eff7f36d410b5c723))
* **deps:** update module golang.org/x/sys to v0.40.0 (main) ([#20378](https://github.com/grafana/loki/issues/20378)) ([9538b20](https://github.com/grafana/loki/commit/9538b2097a4604f49442e5845c2d95498a0110d0))
* **deps:** update module golang.org/x/text to v0.30.0 (main) ([#19781](https://github.com/grafana/loki/issues/19781)) ([61e06a3](https://github.com/grafana/loki/commit/61e06a3150e1d566025eaa09297e7934d7d831a2))
* **deps:** update module golang.org/x/text to v0.31.0 (main) ([#19851](https://github.com/grafana/loki/issues/19851)) ([af03168](https://github.com/grafana/loki/commit/af0316840991424d475cd93ac5e88f626035eeba))
* **deps:** update module golang.org/x/text to v0.33.0 (main) ([#20408](https://github.com/grafana/loki/issues/20408)) ([9fd6733](https://github.com/grafana/loki/commit/9fd6733ef4f9f82ee032728c27229ce00673ddfe))
* **deps:** update module golang.org/x/time to v0.14.0 (main) ([#19782](https://github.com/grafana/loki/issues/19782)) ([74f68fa](https://github.com/grafana/loki/commit/74f68fac62757fc50b295100bb30c7bb4c3007aa))
* **deps:** update module google.golang.org/api to v0.255.0 (main) ([#19792](https://github.com/grafana/loki/issues/19792)) ([aba027b](https://github.com/grafana/loki/commit/aba027b593d9939fb7b2fbc3de92b9dc74d1eb30))
* **deps:** update module google.golang.org/api to v0.256.0 (main) ([#19852](https://github.com/grafana/loki/issues/19852)) ([145b063](https://github.com/grafana/loki/commit/145b0634669a7ad0e8ba026b418ab6b239b69677))
* **deps:** update module google.golang.org/api to v0.257.0 (main) ([#20143](https://github.com/grafana/loki/issues/20143)) ([5f1da75](https://github.com/grafana/loki/commit/5f1da751a4181af9bf11a675bb24f9e8c5cad39c))
* **deps:** update module google.golang.org/grpc to v1.76.0 (main) ([#19422](https://github.com/grafana/loki/issues/19422)) ([2e1c644](https://github.com/grafana/loki/commit/2e1c644780c5e4c336d9bfd1855719527c4581ae))
* **deps:** update module google.golang.org/grpc to v1.77.0 (main) ([#19945](https://github.com/grafana/loki/issues/19945)) ([f3213bb](https://github.com/grafana/loki/commit/f3213bb2f90fe1f8ff4421f400c22820ee41e69b))
* **deps:** update module google.golang.org/protobuf to v1.36.11 (main) ([#20349](https://github.com/grafana/loki/issues/20349)) ([a80b52e](https://github.com/grafana/loki/commit/a80b52e01941693892313c440dd656e72aff4d2c))
* **deps:** update module k8s.io/apimachinery to v0.34.2 (main) ([#19793](https://github.com/grafana/loki/issues/19793)) ([6d4cf98](https://github.com/grafana/loki/commit/6d4cf98bca47bbb8b57303280488077eece0690a))
* **deps:** update module k8s.io/apimachinery to v0.34.3 (main) ([#20187](https://github.com/grafana/loki/issues/20187)) ([d4814ec](https://github.com/grafana/loki/commit/d4814ec00363b796f66d7a1019014362c7943668))
* **deps:** update module k8s.io/apimachinery to v0.35.0 (main) ([#20381](https://github.com/grafana/loki/issues/20381)) ([731e067](https://github.com/grafana/loki/commit/731e067b3abfb463fe59b4d9ebc4e3116d97fd87))
* Do not override S3 region if already specified in configuration chain ([#20127](https://github.com/grafana/loki/issues/20127)) ([0046bfb](https://github.com/grafana/loki/commit/0046bfb3a4c08321a0006d1aa70963e234162404))
* **docker:** missing permissions  to start docker ([#19947](https://github.com/grafana/loki/issues/19947)) ([39d2bea](https://github.com/grafana/loki/commit/39d2beaae6f2867084cb856e353413fe58e066fc))
* **docker:** set WORKDIR to root in loki Dockerfiles ([#19941](https://github.com/grafana/loki/issues/19941)) ([13f2b1a](https://github.com/grafana/loki/commit/13f2b1adaeb12e39d1019aa484488422feb499f1))
* Empty keys are returned if desired in v2 engine ([#19717](https://github.com/grafana/loki/issues/19717)) ([36613bd](https://github.com/grafana/loki/commit/36613bd0175fee1555363e78d08b68fba4f90650))
* **engine:** unset write and read deadlines for wire listeners ([#19828](https://github.com/grafana/loki/issues/19828)) ([9b001df](https://github.com/grafana/loki/commit/9b001dfd01d1b87840ae691c2bf464782c33165a))
* **enginev2:** Always compute summary when creating the stats object ([#20224](https://github.com/grafana/loki/issues/20224)) ([ea88458](https://github.com/grafana/loki/commit/ea88458c03cecf59d872eb3c4b1cf0f44b959491))
* **enginev2:** Close pipeline before building query results ([#20100](https://github.com/grafana/loki/issues/20100)) ([99ba51e](https://github.com/grafana/loki/commit/99ba51e48a52f2db1b954e0f056637e694d79d2e))
* errors in parse pipeline ([#19667](https://github.com/grafana/loki/issues/19667)) ([dd6b314](https://github.com/grafana/loki/commit/dd6b31473e21dcfff5b67a0bdbcaf77ab840fbb0))
* Evaluation time in Goldfish query comparator ([#20425](https://github.com/grafana/loki/issues/20425)) ([e772ef4](https://github.com/grafana/loki/commit/e772ef4f05a7e93de4192e912f5d06780153115e))
* expose RDS args for goldfish ui ([#19724](https://github.com/grafana/loki/issues/19724)) ([b2396e1](https://github.com/grafana/loki/commit/b2396e1fb8332032ee9ce9350940c42885811d3a))
* Fix regression in S3 client configuration ([#20110](https://github.com/grafana/loki/issues/20110)) ([d3f9532](https://github.com/grafana/loki/commit/d3f9532b061c4406bbd5d95c77b5220c0bd80193)), closes [#19908](https://github.com/grafana/loki/issues/19908)
* **goldfish:** add tolerance check to mismatches in the query-tee ([#20004](https://github.com/grafana/loki/issues/20004)) ([581519e](https://github.com/grafana/loki/commit/581519e386b9a80e40502d5ad96948959d641138))
* **helm:** Add startup probe read ([#19708](https://github.com/grafana/loki/issues/19708)) ([bce87fb](https://github.com/grafana/loki/commit/bce87fbce5d518d2785620596ee78898718b1ace))
* **helm:** Apply fix from [#14126](https://github.com/grafana/loki/issues/14126) to example ([#20252](https://github.com/grafana/loki/issues/20252)) ([716563a](https://github.com/grafana/loki/commit/716563a660f079762c8ea8caf5ca78a12e81b314))
* **helm:** correct GEL provisioner tenant creation instructions ([#20271](https://github.com/grafana/loki/issues/20271)) ([9639e2e](https://github.com/grafana/loki/commit/9639e2e1269067fb1e3d13ecfbd7f5350326d606))
* **helm:** Correct GEL version ([#19657](https://github.com/grafana/loki/issues/19657)) ([cd8b195](https://github.com/grafana/loki/commit/cd8b195fd8e278aa7ef44da401ac9c36209575a3))
* **helm:** do not mark loki.storage.bucketNames.chunks as required, if an s3 url is provided ([#19873](https://github.com/grafana/loki/issues/19873)) ([e9951bb](https://github.com/grafana/loki/commit/e9951bb4ebfdd85c4567c67a339edf6d7fb78991))
* **helm:** do not mark loki.storage.bucketNames.chunks as required, if minio is used. ([#19871](https://github.com/grafana/loki/issues/19871)) ([eddd4f8](https://github.com/grafana/loki/commit/eddd4f873de3cfd6a14e349356abc8fa9596a13d))
* **helm:** do not mark loki.storage.bucketNames.ruler as required, if  rulerConfig.storage.type is local ([#19882](https://github.com/grafana/loki/issues/19882)) ([f2f564a](https://github.com/grafana/loki/commit/f2f564a2672df170502760d9c8a0afca2855515b))
* **helm:** Don't fail for missing bucket name, if local disk is used. ([#19675](https://github.com/grafana/loki/issues/19675)) ([ad0a29e](https://github.com/grafana/loki/commit/ad0a29eaae24cbcc385ae5ed39614fbd2765fb27))
* **helm:** Don't fail for missing bucket name, if minio is enabled. ([#19745](https://github.com/grafana/loki/issues/19745)) ([cd0c578](https://github.com/grafana/loki/commit/cd0c5782105c998fe011b9e47f1563c1bf769ccd))
* **helm:** Enable volumeAttributesClassName attributes for volumeClaimTemplates ([#19719](https://github.com/grafana/loki/issues/19719)) ([06da42a](https://github.com/grafana/loki/commit/06da42a8ac203361960ffada560bc44fea257c96))
* **helm:** Fix ingester-b volumeAttributesClassName templating ([#20188](https://github.com/grafana/loki/issues/20188)) ([d696f18](https://github.com/grafana/loki/commit/d696f188165d9bf4c40b60f8baa0c8bc4ed9bf29))
* **helm:** Fix rendering of dnsConfig for backend, read, write, single-binary and table-manager ([#20013](https://github.com/grafana/loki/issues/20013)) ([1cdb3c7](https://github.com/grafana/loki/commit/1cdb3c731819eba5808de55a29b319e09aa00ec0))
* **helm:** Respect global registry in sidecar image ([#18246](https://github.com/grafana/loki/issues/18246)) ([#19347](https://github.com/grafana/loki/issues/19347)) ([79eae2c](https://github.com/grafana/loki/commit/79eae2ca25c8faa262c246bafcf913eb4e8fd2c3))
* **helm:** Update Chart version in README.md ([#19669](https://github.com/grafana/loki/issues/19669)) ([94096b7](https://github.com/grafana/loki/commit/94096b745229fbc653fe6037251e36816f2b76e5))
* **helm:** update version ([#19670](https://github.com/grafana/loki/issues/19670)) ([b90ae22](https://github.com/grafana/loki/commit/b90ae22a2c3da177e334fd16e057fb5e260d1f69))
* logging and failed migrations in query-tee ([#19861](https://github.com/grafana/loki/issues/19861)) ([a000cd1](https://github.com/grafana/loki/commit/a000cd10a07585eff4985f0a6554909a18bfbec5))
* loki_dataobj_sort_duration_seconds never registered ([#19679](https://github.com/grafana/loki/issues/19679)) ([da37290](https://github.com/grafana/loki/commit/da37290a4045e160a71ab6c07c63fa77b07c5bf9))
* **lokitool:** Update ruler path and enable alternative TLS env variables ([#19572](https://github.com/grafana/loki/issues/19572)) ([d1ce5cb](https://github.com/grafana/loki/commit/d1ce5cb6af8cf1cb8063d07fb0c5b841e23b5caf))
* Nomad simple example ([#19629](https://github.com/grafana/loki/issues/19629)) ([17aec11](https://github.com/grafana/loki/commit/17aec119a0af3e1749f38857f35dca18200d0c4f))
* **operator:** change leader-election parameters ([#19707](https://github.com/grafana/loki/issues/19707)) ([86068cf](https://github.com/grafana/loki/commit/86068cfb6c9c221dbb3878bdd5e86a53b6ce2caa))
* **operator:** Do not deploy NetworkPolicies automatically on OCP 4.20 ([#19680](https://github.com/grafana/loki/issues/19680)) ([8df33ff](https://github.com/grafana/loki/commit/8df33ff659d53d17b68fb894879587b330e63607))
* **operator:** Return quickstart script to working condition and improve rootless usage ([#19960](https://github.com/grafana/loki/issues/19960)) ([397da27](https://github.com/grafana/loki/commit/397da277753d771d8c1492dd3f4db4b208b3532d))
* Out of bounds error fix for gapped window matcher ([#20396](https://github.com/grafana/loki/issues/20396)) ([168da48](https://github.com/grafana/loki/commit/168da488dbcfe3bf11d97646639465b41e68d022))
* panic when no healthy instances found ([#19998](https://github.com/grafana/loki/issues/19998)) ([1c5dfed](https://github.com/grafana/loki/commit/1c5dfed23acc4931baa6bdcb1fe49b12e2f77072))
* parsed labels should not override structured metadata ([#19991](https://github.com/grafana/loki/issues/19991)) ([61f9367](https://github.com/grafana/loki/commit/61f936751b185a9e6f7127321c83b1fc1816a067))
* **parser:** do not cache key conflicts results in intern set ([#19984](https://github.com/grafana/loki/issues/19984)) ([0a9b024](https://github.com/grafana/loki/commit/0a9b024106eda89844dbd68e6625b241ab0b1655))
* persist correct goldfish result comparison in database ([#20172](https://github.com/grafana/loki/issues/20172)) ([43a3f15](https://github.com/grafana/loki/commit/43a3f159b3d529d5f4141bf98c5e19a6845ae7da))
* **promtail:** validate relabel config ([#19996](https://github.com/grafana/loki/issues/19996)) ([1bce8ec](https://github.com/grafana/loki/commit/1bce8ecea8910d91e2f287c05a68b4e5054af915))
* **querier:** Support multi-tenant queries in Patterns API ([#19809](https://github.com/grafana/loki/issues/19809)) ([f609e27](https://github.com/grafana/loki/commit/f609e27e2eebaadce3c629c8ad8be054f885a604))
* **querylimits:** accept request limits over not initialized limits ([#19891](https://github.com/grafana/loki/issues/19891)) ([905eac8](https://github.com/grafana/loki/commit/905eac851f38da589c49a41478e2edd2b3bb3ffb))
* **querytee:** forward response headers from backends ([#20036](https://github.com/grafana/loki/issues/20036)) ([2b2f00f](https://github.com/grafana/loki/commit/2b2f00f24cae6bf1db13f852c194958605c3b042))
* reduce FetchMaxBytes to 10MB ([#19883](https://github.com/grafana/loki/issues/19883)) ([82cfafd](https://github.com/grafana/loki/commit/82cfafd3862906e41ab32a03e8cd7f10e8511940))
* remove logging of sensitive data ([#20168](https://github.com/grafana/loki/issues/20168)) ([d7c1e1d](https://github.com/grafana/loki/commit/d7c1e1daa6e8e26e43fdf2682e98fce55702c19c))
* Respect categorizeLabels encoding flag in v2 queries ([#20098](https://github.com/grafana/loki/issues/20098)) ([0dea806](https://github.com/grafana/loki/commit/0dea806656f411251d856dc0acf5efe8db96218d))
* Restrict start/end timestamp to requested range for scheduler ([#20086](https://github.com/grafana/loki/issues/20086)) ([448cc74](https://github.com/grafana/loki/commit/448cc745cab05e8967696e3c24231b4d23ee7715))
* **retry:** do not retry if any of multierrors is a client error ([#19887](https://github.com/grafana/loki/issues/19887)) ([9825137](https://github.com/grafana/loki/commit/9825137713f84ee26de4640084f6ee3d5cc4354d))
* revoke partitions if lost ([#20030](https://github.com/grafana/loki/issues/20030)) ([1ac5d1f](https://github.com/grafana/loki/commit/1ac5d1f0d5e80cbb5e2ea73fed007ea6f80ccf61))
* **ruler:** validate remote write config ([#19920](https://github.com/grafana/loki/issues/19920)) ([e916944](https://github.com/grafana/loki/commit/e9169443760f0e64868f52e8b746f31eadf68f6d))
* Scheduler memory leak ([#20268](https://github.com/grafana/loki/issues/20268)) ([d776c10](https://github.com/grafana/loki/commit/d776c10dff76df57eb7978339e5f84c4629e3f78))
* **server:** return status bad request code for interval limit error ([#19895](https://github.com/grafana/loki/issues/19895)) ([f21f5d5](https://github.com/grafana/loki/commit/f21f5d545f5ce16a12bed556a63ac5c7764559cd))
* Set Content-Type header for JSON responses in serializeHTTPHandler ([#19878](https://github.com/grafana/loki/issues/19878)) ([019d6b4](https://github.com/grafana/loki/commit/019d6b40a84ff0de1e835ba111efe121c966cf2d))
* track discarded entries and bytes when hitting stream limits using the ingest limits service ([#20244](https://github.com/grafana/loki/issues/20244)) ([9b0af7c](https://github.com/grafana/loki/commit/9b0af7c002b8a8e87fe1e3ec2817d06641e099d3))
* use the default downstream handler for unsupported requests ([#20202](https://github.com/grafana/loki/issues/20202)) ([0a34e25](https://github.com/grafana/loki/commit/0a34e25deae721b2dd5414f0819747cf37e73169))


### Miscellaneous Chores

* **engine:** Make scheduler aware of total compute capacity ([#19876](https://github.com/grafana/loki/issues/19876)) ([e9600ae](https://github.com/grafana/loki/commit/e9600aed4b78cbf007c9e93771610cb6a8b3ff79))
* **engine:** Share worker threads across all scheduler connections ([#20229](https://github.com/grafana/loki/issues/20229)) ([eaeb7af](https://github.com/grafana/loki/commit/eaeb7afe8899fdac88285d49a94d0b565696ab59))


================================================================================

# v3.7.1

Tag: v3.7.1
URL: https://github.com/grafana/loki/releases/tag/v3.7.1

## [3.7.1](https://github.com/grafana/loki/compare/v3.7.0...v3.7.1) (2026-03-26)


### Bug Fixes

* Upgrade Go and gRPC versions on 3.7.x ([#21282](https://github.com/grafana/loki/issues/21282)) ([2c8fff2](https://github.com/grafana/loki/commit/2c8fff222bab6813374b973ae0eb49043d3ed14e))

