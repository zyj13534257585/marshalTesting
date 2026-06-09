"""
Marshal 往返哈希值兼容性测试

测试当前 Python 环境下的 marshal 往返哈希值与基准哈希值是否一致
"""

import sys
import marshal
import hashlib
import math
import random
import os
import json
from datetime import datetime
from typing import Any, Dict, List, Tuple

# =====================================================
# 基准哈希值（从 Python 3.13.13 采集）
# =====================================================

MARSHAL_ROUNDTRIP_BASELINE_HASHES = {
    "None": "dc937b59892604f5a86ac96936cd7ff09e25f18ae6b758e8014a24c7fa039e91",
    "True": "3cbc87c7681f34db4617feaa2c8801931bc5e42d8d0f560e756dd4cd92885f18",
    "False": "60a33e6cf5151f2d52eddae9685cfa270426aa89d8dbc7dfb854606f1d1a40fe",
    "Zero": "5feceb66ffc86f38d952786c6d696c79c2dbc239dd4e91b46729d73a27fb57e9",
    "SmallInt": "73475cb40a568e8da8a045ced110137e159f890ac4da883b6b17dc651b3a8049",
    "LargeInt": "5ee7924f903dfefa9253b5f63147f53433516da9daf01f6e729331dcf31b28c6",
    "NegativeInt": "98557f4b4ff595debf238559844f4309ea71ba62ce3c0ac65d6ab608f05d65ff",
    "Float": "c0740dd25c9de39b9c8d5ab452e8b69bcc0bf86f2a60ed7e527e79d0a3035852",
    "String": "c3a5789ee2dd379f5136ee028030c1b090fbda5d290bfedd06d816f5a142d43b",
    "EmptyString": "6f49cdbd80e1b95d5e6427e1501fc217790daee87055fa5b4e71064288bddede",
    "Unicode": "4f955db98d7a2f45313647424d566449f78a4d2d423edf58a91a718370c30687",
    "Bytes": "1ff632a611885373673516162c18b64c8c57ac5b1a3e60c0a3facba0e7645a31",
    "EmptyBytes": "1df8639a53769df8d7c936f1247facdff4636e11b43d7b868f96709eb67235d5",
    "Complex": "a8400f1c19a4630c1bfb794a66c5d60ee57cb4ffcf8c14047a8bb2ae09a289b2",
    "EmptyList": "2e38e77b22c314a449e91fafed92a43826ac6aa403ae6a8acb6cf58239fbaf5d",
    "List": "99981198c62def3931cf4ef3dff94963a719e584424fda29598ea00d264fb3c5",
    "NestedList": "4789913894fe14dac334fec89e6a3e414ac2c53f3ff9b38010d7aba598c5568f",
    "EmptyTuple": "2e38e77b22c314a449e91fafed92a43826ac6aa403ae6a8acb6cf58239fbaf5d",
    "Tuple": "dfd5726d86ed2c8b202855bbea88990ec37a26ab1d2217b55a61b4b6719ff6fd",
    "SingletonTuple": "28cb03b06c288e88c6a880eeba293bf9c9bb9fa586128586459a486a511f832f",
    "EmptyDict": "2e38e77b22c314a449e91fafed92a43826ac6aa403ae6a8acb6cf58239fbaf5d",
    "Dict": "85b5bcfbe112ff611ec04da9920e5de4dc7a53e0136755683f69d02aaecc6495",
    "NestedDict": "d66796352351a8aee62c915b567dcfb6f94ce87f316f31e7f30a64af1349502c",
    "EmptySet": "9153e9848cc4ff2e87f47ff5f55a64467c26c87b0d2eb9edf49b38c8f5a96049",
    "Set": "b7697bfd38813aaaa3439456eb0f4ebc30e2e465f5ab58070123c445de3c381e",
    "EmptyFrozenSet": "9153e9848cc4ff2e87f47ff5f55a64467c26c87b0d2eb9edf49b38c8f5a96049",
    "FrozenSet": "b7697bfd38813aaaa3439456eb0f4ebc30e2e465f5ab58070123c445de3c381e",
    "FloatZero": "8aed642bf5118b9d3c859bd4be35ecac75b6e873cce34e7b6f554b06f75550d7",
    "FloatNegZero": "c26617c7ccbcaa6631b45d851b8cf56e21d2ca624bdb1193afdbd4b560702cec",
    "FloatInf": "87e88be45a19fd083c8723f9931cd8bb78717103288f75eb08b3c5090f12a495",
    "FloatNegInf": "fdd14acdcedafbd250650435c171252b0613086d1c4bb7e1a885c07188d4115c",
    "FloatNaN": "06a0d93b5dd6f3185d7e826aed7f1277d372dd70df9d24b9f6f3c45f5c7324e0",
    "FloatEpsilon": "8d51a73768cb59d15302f6b0a4c7147a04b0cce9df743b5bf50e31ab87b2d807",
    "FloatMax": "c2784e1abd6317452708f3fbf9641c16b959561bc621a1d408c23a20aa2cb585",
    "SelfReferentialList": "d77105626a6c7416c78bc6bb583d35560e158f58dac24718da9cf23f06e2fe85",
    "SelfReferentialDict": "ba5fe04b4870548bdc6cd91517781a0feb8150ef0ed35966a575fb1ef621bd55",
    "MutualReference": "00c8e095671a437974627e2a698ab281c87bcaffe72147f07d73fb0e4db1aaae",
    "TripleCycle": "d1425a03454ed86e94bef643487c87942ba4c97ee38bb696d2d3ae36a551e916",
    "CycleInTuple": "54ebf71264ad7e299c3ee09246c65524695f6e0118ee829749dc78f9a2855551",
    "CycleInDict": "6fce5ac1882ae0e47b47a3093160c20f51d452a55e4c46494a034a8437f273ac",
    "DeepRecursion_50": "f20e4e64ef01eba18f91ab43538d5bc80cfb17426a5e560d28b5a2623f721ea8",
    "IntMinus1": "1bad6b8cf97131fceab8543e81f7757195fbb1d36b376ee994ad1cf17699c464",
    "Int0": "5feceb66ffc86f38d952786c6d696c79c2dbc239dd4e91b46729d73a27fb57e9",
    "Int1": "6b86b273ff34fce19d6b804eff5a3f5747ada4eaa22f1d49c01e52ddb7875b4b",
    "Int2_31_Minus1": "972dcafa6fb4c2c88bce752fca4ab18c6bd88599330a4ad9813915b05bfbe76d",
    "IntNeg2_31": "56bb3b3a6aa1747def7c225256374c5e73f2fc46555adc47ea16e2d782159387",
    "Int2_31": "39f8d58187887b481fe709f7b323f2b876d9f522e9f7afef815c2089084a36d7",
    "Int2_63_Minus1": "b34a1c30a715f6bf8b7243afa7fab883ce3612b7231716bdcbbdc1982e1aed29",
    "IntNeg2_63": "85386477f3af47e4a0b308ee3b3a688df16e8b2228105dd7d4dcd42a9807cb78",
    "Int2_63": "c5c29af0c2b1ba23907ca40686689919361601e7740335050476b290f2f87ee8",
    "Int2_1000": "8c5d0b143c6a93c64bcd6f29fedfeea73a7198430f420372155ed5ace8c25e0a",
    "StringEmpty": "6f49cdbd80e1b95d5e6427e1501fc217790daee87055fa5b4e71064288bddede",
    "String1Char": "d749929fe94b9a37dbe5d74cb297ad24b46e467898545f4e109eb21835046ac4",
    "String255": "f4032d9e431a79e4cf915d51608022818323ede7b2583756044e807c02f687c5",
    "String256": "0ac5c4713de58f9c3a093ab6be760a910062960f4b1210575b57ba487ada5fd4",
    "String65535": "08fc33a658fa8480668f847572a730ca63f4610f56106a47d6badb607c1c1585",
    "String65536": "ee12ed033a4cfcb473072fefebe51c36911f4c84c311b87690355d7782f0fac3",
    "StringUnicode1": "af68a844f762bdde2602046c2b79a33649bbac144177a80700c747aa63838db4",
    "StringUnicode1000": "638335d0bf0c55f5dba8c95791e90a2a86eb5e0b402c1c6a3fd2813db738fa8d",
    "ListEmpty": "2e38e77b22c314a449e91fafed92a43826ac6aa403ae6a8acb6cf58239fbaf5d",
    "List1Elem": "28cb03b06c288e88c6a880eeba293bf9c9bb9fa586128586459a486a511f832f",
    "ListLarge": "545f66570f4cc39a3cc0be33a6d1930729b5ba724016d12a00c99d5f73b066d5",
    "DictEmpty": "2e38e77b22c314a449e91fafed92a43826ac6aa403ae6a8acb6cf58239fbaf5d",
    "Dict1Elem": "4f798fe9c78df93aa1bcc261edbd3e1e9b716ab581158271dd62421072c7f624",
    "DictLarge": "003475a7e20d746f636beaebf8f99394d8c28a9bba3427944db1acc189e0d5b7",
    "TupleEmpty": "2e38e77b22c314a449e91fafed92a43826ac6aa403ae6a8acb6cf58239fbaf5d",
    "Tuple1Elem": "28cb03b06c288e88c6a880eeba293bf9c9bb9fa586128586459a486a511f832f",
    "TupleLarge": "545f66570f4cc39a3cc0be33a6d1930729b5ba724016d12a00c99d5f73b066d5",
    "TypeNone": "dc937b59892604f5a86ac96936cd7ff09e25f18ae6b758e8014a24c7fa039e91",
    "TypeBool_True": "3cbc87c7681f34db4617feaa2c8801931bc5e42d8d0f560e756dd4cd92885f18",
    "TypeBool_False": "60a33e6cf5151f2d52eddae9685cfa270426aa89d8dbc7dfb854606f1d1a40fe",
    "TypeInt_Small": "73475cb40a568e8da8a045ced110137e159f890ac4da883b6b17dc651b3a8049",
    "TypeInt_Large": "5ee7924f903dfefa9253b5f63147f53433516da9daf01f6e729331dcf31b28c6",
    "TypeFloat": "c0740dd25c9de39b9c8d5ab452e8b69bcc0bf86f2a60ed7e527e79d0a3035852",
    "TypeFloat_Inf": "87e88be45a19fd083c8723f9931cd8bb78717103288f75eb08b3c5090f12a495",
    "TypeFloat_NaN": "06a0d93b5dd6f3185d7e826aed7f1277d372dd70df9d24b9f6f3c45f5c7324e0",
    "TypeComplex": "a8400f1c19a4630c1bfb794a66c5d60ee57cb4ffcf8c14047a8bb2ae09a289b2",
    "TypeString": "d543699194a3343443ab84395c0464b018f12e31df1b5e829d65c4440e90b9a5",
    "TypeString_Long": "d783b8c7cb2cbf646e79e50f49610888725dffe87602da55df4835f471902344",
    "TypeUnicode": "166c1c92757bf6094d38191cece920f0713705b3dce3d318fc30cffc8c7d6286",
    "TypeTuple": "dfd5726d86ed2c8b202855bbea88990ec37a26ab1d2217b55a61b4b6719ff6fd",
    "TypeList": "dfd5726d86ed2c8b202855bbea88990ec37a26ab1d2217b55a61b4b6719ff6fd",
    "TypeDict": "aa80bcaca15ad650a5c82452ca529801ec0444fd334383f9b31ef9c2a70bcfba",
    "TypeDict_IntKeys": "4eb9f1b714cbecf79b7871147f6300ed15ec9baf2b9d53bfc0e0bf91aed71f4f",
    "TypeSet": "b7697bfd38813aaaa3439456eb0f4ebc30e2e465f5ab58070123c445de3c381e",
    "TypeFrozenSet": "b7697bfd38813aaaa3439456eb0f4ebc30e2e465f5ab58070123c445de3c381e",
    "TypeRef": "d77105626a6c7416c78bc6bb583d35560e158f58dac24718da9cf23f06e2fe85",
    "Fuzz_1": "95cf3b70fe5e8606eef2161db124ad27d7d143a9a7156d1623ea2612f91bb58f",
    "Fuzz_2": "dd57e71b5707bed274cf53fe5c3ce3608d26f8513d1b94ed8f66a6707b9fc7d0",
    "Fuzz_3": "b3e50d0021a45c36ef80132bc86e07be55ac72f2580c9710d4b3fbbec97477c2",
    "Fuzz_4": "1ec1fb2d0bf20642140b795ed899c4c8bdafd876367a3938cf45781fd0a6ab40",
    "Fuzz_5": "dc937b59892604f5a86ac96936cd7ff09e25f18ae6b758e8014a24c7fa039e91",
    "Fuzz_6": "60a33e6cf5151f2d52eddae9685cfa270426aa89d8dbc7dfb854606f1d1a40fe",
    "Fuzz_7": "2e38e77b22c314a449e91fafed92a43826ac6aa403ae6a8acb6cf58239fbaf5d",
    "Fuzz_8": "3f9403ecc8fc3c2eb64a12c6004f464294fcc7013b1c5e163430630c95b96b7e",
    "Fuzz_9": "86ef961407bfd28d1f8f9bb6081e957eadcb473a1decc342e46aef10d867519c",
    "Fuzz_10": "9153e9848cc4ff2e87f47ff5f55a64467c26c87b0d2eb9edf49b38c8f5a96049",
    "Fuzz_11": "7c41f163a715d4ffd2cb9e2f6a803fae045a4acc9307e38b150fb8eb785dfd3f",
    "Fuzz_12": "29ff5ad9fe7e2f84a650645f172b87c2b15e087272c0501fd035e22d10e57c28",
    "Fuzz_13": "e593cd88956b73b43b08ccd40af99becbdd98262ac1388ad765e7bda0b59f6e1",
    "Fuzz_14": "8c0d0bfabc9789d08e800c73793269805d8f3bdbacdb99963d923554615d81f7",
    "Fuzz_15": "9615893a6914208efb30b5a96806bbda66e5049fb4c483527aadd5a00e162324",
    "Fuzz_16": "b2122931f4ce448403c9e5b62fb94547b580a069c5369f6ef9b688c56615c032",
    "Fuzz_17": "18511b8b19cff89eb2c88cf0b76fa1a1c4046528ac15173befdd05c62bc5e353",
    "Fuzz_18": "e97fce57e372bdb44f5aa329dc4a8df7eaf6b8f5d509e9204054ff0bbc02a7e2",
    "Fuzz_19": "9214daaa4accaed55eb5f3385b84966d7f0ad8ab7ea096be226ebe0060abff96",
    "Fuzz_20": "2e38e77b22c314a449e91fafed92a43826ac6aa403ae6a8acb6cf58239fbaf5d",
    "Fuzz_21": "6ba9fb596edfa9d11b5b99d38ddb8a8884264ace770b12faef6f9285714dbc86",
    "Fuzz_22": "d5453781b51a80163f03fc9257a029c240fbf45691f68662daebb7e17dccbaa2",
    "Fuzz_23": "7030e9919631b917c109e70b97e5fb550391432880cdcef6e43c41f56a6b9de6",
    "Fuzz_24": "297d5d7dcf0664202b25983b2d08bba442dd2edf26013e3533784a7a5f94a971",
    "Fuzz_25": "89dc95dd79d410bc18a13a64673cd7cb7b99a58a1de96e982af4e6856de079e8",
    "Fuzz_26": "482b6e2da83c3ce8544f900d746b42ccca0d0890140188995f427f310bb1de19",
    "Fuzz_27": "78a83e17fc0723b8329dd820cb609542a606133b8c5adb0edb07b4bf1e37a8cf",
    "Fuzz_28": "1037eaacfef47438c2c87e944caeac89b4c26b5f714d2fc655c8554f0f1bc0e2",
    "Fuzz_29": "ff0e92561408830a37d7bf32f0416a9b95fdea3180d0a8d905b910261f95c640",
    "Fuzz_30": "35f5c86c92ee8eb60def93a35247053210400ff43136f6e7cf39dcbdc80e69fb",
    "Fuzz_31": "57103a9f0646fc904c0b0e49b9dbacddf525985370b9c1051ac89765e79ded78",
    "Fuzz_32": "a10df479049dd839097b2763ee5431e5b2f16d76c6f762a0f75f8cb4276d8da3",
    "Fuzz_33": "41fee9d771f1c77ec5604ec063f4329033aca88797827a7e96a6296a8e329978",
    "Fuzz_34": "a3d1eabfad90467b7b120b17505c35d91c52a71c2e08ec40df69afd0f562f4f8",
    "Fuzz_35": "9153e9848cc4ff2e87f47ff5f55a64467c26c87b0d2eb9edf49b38c8f5a96049",
    "Fuzz_36": "2e38e77b22c314a449e91fafed92a43826ac6aa403ae6a8acb6cf58239fbaf5d",
    "Fuzz_37": "97c9abefb2a7ab2863bdc8fcb0e355d635d79d4c3732bf966a944bcc16fafd0d",
    "Fuzz_38": "488c05b26d89053eafb27aadf1de5ebb4e643788cc0d5a0c421a5b6c585dbd85",
    "Fuzz_39": "7f048e7612f1b4d72e24a62d3aca61eb4e893abe8dc52aecdb97e76b4d089b6e",
    "Fuzz_40": "87e88be45a19fd083c8723f9931cd8bb78717103288f75eb08b3c5090f12a495",
    "Fuzz_41": "2e38e77b22c314a449e91fafed92a43826ac6aa403ae6a8acb6cf58239fbaf5d",
    "Fuzz_42": "ff1e7b4ce3a9b3771e17b4f734ff67b54b9e1e035400daefb210cb69e159200c",
    "Fuzz_43": "74c3aa81acab965b89369f1e4bd816c04f8a00fe84cf2bf57e0904ae9332b3c7",
    "Fuzz_44": "e1ada9f1b04b9b18114f82904544de85f93e35aea1518b436e00775e269f4afe",
    "Fuzz_45": "368f96e8be34d39b019bcd255f0383668caa79167e51c1d8d3b08fca6b7bfce7",
    "Fuzz_46": "9153e9848cc4ff2e87f47ff5f55a64467c26c87b0d2eb9edf49b38c8f5a96049",
    "Fuzz_47": "88bb7789c75d436cbc0fd8cb7f1f32ae0aa5a56bacf4c80747e9318697996b60",
    "Fuzz_48": "9153e9848cc4ff2e87f47ff5f55a64467c26c87b0d2eb9edf49b38c8f5a96049",
    "Fuzz_49": "9a491243b2d594041f60bc3c2211b0a092d0168642bf9156de1d5a311f10e395",
    "Fuzz_50": "92994e4ec32365c290d68ea1d4e2953dd77e079ba8b98963bf90e033ec4345fb",
    "Fuzz_51": "7f0042fef69c764547c82e7cc4a7eb5f08301ad927721e8f76d4f09c71d75b02",
    "Fuzz_52": "9d6f56ebd4382995382b0276cacb6a450b12205e38e8d481ebfd8c6baabcf367",
    "Fuzz_53": "254f1e08e8161f1e4f314ef04f127a46058e947887fc9380bd879f7f7b72d737",
    "Fuzz_54": "64a5b604af71797323d45061607f96f9bf41cde461fa9e12db3fdac095aceaa3",
    "Fuzz_55": "d671ccaab8c6f896636b0c84671a82c39e1fb97ae7f26fde01657780870d1d2f",
    "Fuzz_56": "391c5169d54960da20a44ede2ed278878a832143fcaa263c3accc97c90d425be",
    "Fuzz_57": "efc6ea1b9f48cfa235568b8e373a958e851a45ab49e303149e3401c752472442",
    "Fuzz_58": "dc937b59892604f5a86ac96936cd7ff09e25f18ae6b758e8014a24c7fa039e91",
    "Fuzz_59": "821dc0caa74d4caf7d8b6209ad75d699562cafbc4c6e775dec529ada18336ddd",
    "Fuzz_60": "3cbc87c7681f34db4617feaa2c8801931bc5e42d8d0f560e756dd4cd92885f18",
    "Fuzz_61": "b5772dab09872727be2f34f696722f09d5b3f3043bbd3f016e83c15b64c5b538",
    "Fuzz_62": "aef0904735a9f6128e87bf2cd4962d1279d84c96f3951611ef30985c6d09bb42",
    "Fuzz_63": "fd67e35aff41e79ebe1fa5f977dd3c3fa2695eaa9758d853d2b0533b8ba6f8ef",
    "Fuzz_64": "5770660846da726269043e254bea4440cfd5e3489afb1b51a071f9870e45b631",
    "Fuzz_65": "dc937b59892604f5a86ac96936cd7ff09e25f18ae6b758e8014a24c7fa039e91",
    "Fuzz_66": "bd9d91bc60873726aa790ea6f744c8af648024d978e10ed290cc5bffb5180af2",
    "Fuzz_67": "3cbc87c7681f34db4617feaa2c8801931bc5e42d8d0f560e756dd4cd92885f18",
    "Fuzz_68": "5e2fbdbfac2a26066191e31815be477b1d7bdea49c7fc967bbc1748b4e171b7b",
    "Fuzz_69": "06ea7b9fb58d69ee421c60274d14c2f031c371cbf046b0a6f20f3bfdc19ec78d",
    "Fuzz_70": "4160b3757df802a741c1b682bcf307dded4af1eeef9c3e59aeb7953dbec7b76f",
    "Fuzz_71": "3c48b0bc30eaee67210ca4513601940d8ecfb8abf495c46e65e7c45af4254a2f",
    "Fuzz_72": "390ee9a6b9f57da38f4f3df94709767c04964824c70e4463143dace5c7366dcd",
    "Fuzz_73": "200025d705a6c2a4b7b76bc4b3dd277e37ebe79ccf941e5b767c198c11cd9775",
    "Fuzz_74": "2e38e77b22c314a449e91fafed92a43826ac6aa403ae6a8acb6cf58239fbaf5d",
    "Fuzz_75": "6af22f1bc2d94295cb210c6a0734b0d7459c92909665da49d949785ecea55bf8",
    "Fuzz_76": "e911473b1dfed8dee43b1a84e245caf0324b6166d24e6cd0f5db7a3f813b211a",
    "Fuzz_77": "d8326c10b5de5f8f8a7cc98624770cf0106b6a0fc79b43aca4c9ee52f5bdee8f",
    "Fuzz_78": "dc937b59892604f5a86ac96936cd7ff09e25f18ae6b758e8014a24c7fa039e91",
    "Fuzz_79": "c27faa0b2e39c805f8dcd5537aa4c3afda1daeca531d335f489149a9b1a3bac7",
    "Fuzz_80": "6093155c85caf9450f9f9f93aa82aac61ebe0451877cc406d41d5d8aa0630e5f",
    "Fuzz_81": "cdccc5f742c31b1cec1ba14a3621f935a0d423627eb9496bf83fa825668f669e",
    "Fuzz_82": "6314b263a4727f00a17fb4ec5c5c50317e05aca16075a1dc519045e9470e031f",
    "Fuzz_83": "4fde1d0d9f57b5a83cd8298c9ae1d3fe1212adb4819c092fcdf1ba165c8d4191",
    "Fuzz_84": "0c1c6eeae2ee6ba1f5457a8fed9a7585ab0c90d96cd0c954345fdf964dac23d4",
    "Fuzz_85": "b379a436cf641c28e8cab9009f8c5a3ac5a6c5939c832530fcf0dd2e3f6261f7",
    "Fuzz_86": "244d91beee47325a555087f8fbe7cf9cc713e2f8c0a53b6c0ef3d81f97a8de5c",
    "Fuzz_87": "ea711cf78574756c064f5e941f2374d54083d7fac3c35b308c7fcdc3c25e314f",
    "Fuzz_88": "dc937b59892604f5a86ac96936cd7ff09e25f18ae6b758e8014a24c7fa039e91",
    "Fuzz_89": "60a33e6cf5151f2d52eddae9685cfa270426aa89d8dbc7dfb854606f1d1a40fe",
    "Fuzz_90": "e45bdcc6e9f4c4b93d7f593e5d252c824f904b439bac44da21a80c3ec47c013f",
    "Fuzz_91": "7a7baab8b58af0e8f5b16348e9e97b8a918e3af6e73658bd9234dbc6249ed8ec",
    "Fuzz_92": "394f6e0da15bd2400a6f925eae2b6a6bc1bac5a30da28d6b451f861cc4f5f115",
    "Fuzz_93": "5ed137023863f729410d046d3139aebc067e73c0a3ea4c6e7b70666fc3db7699",
    "Fuzz_94": "3873655e7315bed2100c177a13cc85fe58cedaf1d11cac979bff8fef3687bcb7",
    "Fuzz_95": "5f82f6ec7858b20866de889f113e592ccf4c3fb998610200ca16bf4db616d381",
    "Fuzz_96": "23ba65ab3e31fb9720a5aff7b97161e48cd890192a6ae3d845a5feeb02893214",
    "Fuzz_97": "fdd14acdcedafbd250650435c171252b0613086d1c4bb7e1a885c07188d4115c",
    "Fuzz_98": "28be6f4c0c0987aebf3146326f0f936cda327a330d52b898ca0af7efa30802e4",
    "Fuzz_99": "e62b419cfa0de434dc9d604fb98f30e64bce19f729417aac9f049ed6b9532051",
    "Fuzz_100": "dee8e025d41fb63a4d364189553b50cd10bc28d2442de83c3075259f6c1bc9a2",
}

# =====================================================
# 从 marshal_cross.py 复制的测试用例生成函数
# =====================================================

MAX_RECURSION_DEPTH = 100

def _get_determinism_test_cases() -> List[Tuple[str, Any]]:
    """获取确定性测试用例"""
    test_cases = []
    
    basic_cases = [
        ("None", None), ("True", True), ("False", False), ("Zero", 0),
        ("SmallInt", 42), ("LargeInt", 2**100), ("NegativeInt", -12345),
        ("Float", 3.14159), ("String", "hello world"), ("EmptyString", ""),
        ("Unicode", "你好世界 🌍"), ("Bytes", b"hello"), ("EmptyBytes", b""),
        ("Complex", 1+2j),
    ]
    test_cases.extend(basic_cases)
    
    container_cases = [
        ("EmptyList", []), ("List", [1, 2, 3, 4, 5]),
        ("NestedList", [1, [2, [3, [4]]]]), ("EmptyTuple", ()),
        ("Tuple", (1, 2, 3)), ("SingletonTuple", (1,)), ("EmptyDict", {}),
        ("Dict", {"a": 1, "b": 2, "c": 3}), ("NestedDict", {"a": {"b": {"c": 1}}}),
        ("EmptySet", set()), ("Set", {1, 2, 3}), ("EmptyFrozenSet", frozenset()),
        ("FrozenSet", frozenset([1, 2, 3])),
    ]
    test_cases.extend(container_cases)
    
    float_cases = [
        ("FloatZero", 0.0), ("FloatNegZero", -0.0), ("FloatInf", float("inf")),
        ("FloatNegInf", float("-inf")), ("FloatNaN", float("nan")),
        ("FloatEpsilon", 2.2250738585072014e-308),
        ("FloatMax", 1.7976931348623157e+308),
    ]
    test_cases.extend(float_cases)
    
    return test_cases


def _get_recursive_test_cases() -> List[Tuple[str, Any]]:
    """获取递归/循环引用测试用例"""
    test_cases = []
    
    self_list = []
    self_list.append(self_list)
    test_cases.append(("SelfReferentialList", self_list))
    
    self_dict = {}
    self_dict["self"] = self_dict
    test_cases.append(("SelfReferentialDict", self_dict))
    
    a = []
    b = [a]
    a.append(b)
    test_cases.append(("MutualReference", a))
    
    x, y, z = [], [], []
    x.append(y)
    y.append(z)
    z.append(x)
    test_cases.append(("TripleCycle", x))
    
    cycle_tuple = ()
    lst = [cycle_tuple]
    cycle_tuple = (lst,)
    lst[0] = cycle_tuple
    test_cases.append(("CycleInTuple", cycle_tuple))
    
    cycle_dict = {}
    lst = [cycle_dict]
    cycle_dict["list"] = lst
    test_cases.append(("CycleInDict", cycle_dict))
    
    depth = min(MAX_RECURSION_DEPTH, 50)
    deep = []
    current = deep
    for i in range(depth):
        current.append([])
        current = current[-1]
    test_cases.append((f"DeepRecursion_{depth}", deep))
    
    return test_cases


def _get_boundary_test_cases() -> List[Tuple[str, Any]]:
    """获取边界值测试用例"""
    test_cases = []
    
    int_boundaries = [
        ("IntMinus1", -1), ("Int0", 0), ("Int1", 1),
        ("Int2_31_Minus1", 2**31 - 1), ("IntNeg2_31", -(2**31)),
        ("Int2_31", 2**31), ("Int2_63_Minus1", 2**63 - 1),
        ("IntNeg2_63", -(2**63)), ("Int2_63", 2**63), ("Int2_1000", 2**1000),
    ]
    test_cases.extend(int_boundaries)
    
    string_boundaries = [
        ("StringEmpty", ""), ("String1Char", "a"), ("String255", "a" * 255),
        ("String256", "a" * 256), ("String65535", "a" * 65535),
        ("String65536", "a" * 65536), ("StringUnicode1", "中"),
        ("StringUnicode1000", "中" * 1000),
    ]
    test_cases.extend(string_boundaries)
    
    list_boundaries = [
        ("ListEmpty", []), ("List1Elem", [1]), ("ListLarge", list(range(10000))),
    ]
    test_cases.extend(list_boundaries)
    
    dict_boundaries = [
        ("DictEmpty", {}), ("Dict1Elem", {"a": 1}),
        ("DictLarge", {str(i): i for i in range(1000)}),
    ]
    test_cases.extend(dict_boundaries)
    
    tuple_boundaries = [
        ("TupleEmpty", ()), ("Tuple1Elem", (1,)), ("TupleLarge", tuple(range(10000))),
    ]
    test_cases.extend(tuple_boundaries)
    
    return test_cases


def _get_whitebox_test_cases() -> List[Tuple[str, Any]]:
    """获取白盒测试用例"""
    test_cases = [
        ("TypeNone", None), ("TypeBool_True", True), ("TypeBool_False", False),
        ("TypeInt_Small", 42), ("TypeInt_Large", 2**100), ("TypeFloat", 3.14159),
        ("TypeFloat_Inf", float("inf")), ("TypeFloat_NaN", float("nan")),
        ("TypeComplex", 1+2j), ("TypeString", "hello"), ("TypeString_Long", "a" * 1000),
        ("TypeUnicode", "你好世界"), ("TypeTuple", (1, 2, 3)), ("TypeList", [1, 2, 3]),
        ("TypeDict", {"a": 1, "b": 2}), ("TypeDict_IntKeys", {1: "a", 2: "b"}),
        ("TypeSet", {1, 2, 3}), ("TypeFrozenSet", frozenset([1, 2, 3])),
    ]
    
    self_ref = []
    self_ref.append(self_ref)
    test_cases.append(("TypeRef", self_ref))
    
    return test_cases


def _get_fuzzing_test_cases(fuzz_count=100, seed=42) -> List[Tuple[str, Any]]:
    """生成模糊测试用例"""
    random.seed(seed)
    test_cases = []
    
    for i in range(fuzz_count):
        obj = _generate_random_object(max_depth=3)
        test_cases.append((f"Fuzz_{i+1}", obj))
    
    return test_cases


def _generate_random_object(max_depth: int = 3) -> Any:
    """递归生成随机对象"""
    if max_depth <= 0 or random.random() < 0.3:
        return _generate_random_primitive()
    
    container_type = random.choice(["list", "dict", "tuple", "set", "frozenset"])
    size = random.randint(0, 5)
    
    if container_type == "list":
        return [_generate_random_object(max_depth - 1) for _ in range(size)]
    if container_type == "dict":
        return {_generate_random_primitive_string(): _generate_random_object(max_depth - 1) for _ in range(size)}
    if container_type == "tuple":
        return tuple(_generate_random_object(max_depth - 1) for _ in range(size))
    if container_type == "set":
        return {_generate_random_primitive() for _ in range(size)}
    if container_type == "frozenset":
        return frozenset(_generate_random_primitive() for _ in range(size))
    
    return _generate_random_primitive()


def _generate_random_primitive() -> Any:
    """生成随机基本类型"""
    choice = random.choice(["none", "bool", "int", "float", "str", "bytes", "complex"])
    
    if choice == "none":
        return None
    if choice == "bool":
        return random.choice([True, False])
    if choice == "int":
        return random.randint(-10**6, 10**6)
    if choice == "float":
        special = random.choice([None, "inf", "-inf", "nan"])
        if special == "inf":
            return float("inf")
        if special == "-inf":
            return float("-inf")
        if special == "nan":
            return float("nan")
        return random.uniform(-1e6, 1e6)
    if choice == "str":
        length = random.randint(0, 20)
        return ''.join(chr(random.randint(32, 126)) for _ in range(length))
    if choice == "bytes":
        length = random.randint(0, 20)
        return bytes(random.randint(0, 255) for _ in range(length))
    if choice == "complex":
        return complex(random.uniform(-100, 100), random.uniform(-100, 100))
    
    return None


def _generate_random_primitive_string() -> str:
    """生成随机字符串"""
    length = random.randint(1, 10)
    return ''.join(chr(random.randint(32, 126)) for _ in range(length))


def safe_marshal_roundtrip(obj: Any) -> Any:
    """安全的 marshal 往返"""
    old_limit = sys.getrecursionlimit()
    try:
        sys.setrecursionlimit(10000)
        data = marshal.dumps(obj)
        restored = marshal.loads(data)
        return restored
    finally:
        sys.setrecursionlimit(old_limit)


def normalize_for_hash(o):
    """将对象标准化以便计算哈希"""
    if isinstance(o, float) and math.isnan(o):
        return "NaN"
    if isinstance(o, float) and math.isinf(o):
        return f"Inf_{math.copysign(1, o)}"
    if isinstance(o, complex):
        if math.isnan(o.real) or math.isnan(o.imag):
            return f"complex({normalize_for_hash(o.real)}, {normalize_for_hash(o.imag)})"
    if isinstance(o, (list, tuple)):
        return tuple(normalize_for_hash(x) for x in o)
    if isinstance(o, dict):
        return tuple(sorted((normalize_for_hash(k), normalize_for_hash(v)) for k, v in o.items()))
    if isinstance(o, (set, frozenset)):
        return frozenset(normalize_for_hash(x) for x in o)
    return o


def hash_object(obj: Any) -> str:
    """计算对象的哈希值"""
    try:
        normalized = normalize_for_hash(obj)
        return hashlib.sha256(repr(normalized).encode()).hexdigest()
    except:
        try:
            data = marshal.dumps(obj)
            return hashlib.sha256(data).hexdigest()
        except:
            return None


def save_inconsistent_results(current_version: str, differences: List[Dict], output_dir: str = "result"):
    """保存不一致的结果到文件"""
    # 创建 result 文件夹
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    version_safe = current_version.replace(" ", "_").replace(".", "_")
    filename = f"inconsistent_{version_safe}_{timestamp}.json"
    filepath = os.path.join(output_dir, filename)
    
    # 准备保存的数据
    save_data = {
        "test_info": {
            "current_python_version": current_version,
            "baseline_python_version": "3.13.13",
            "test_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "total_inconsistent_count": len(differences)
        },
        "inconsistent_cases": []
    }
    
    for diff in differences:
        case_data = {
            "test_case_name": diff["name"],
            "baseline_hash_py313": diff.get("baseline", "N/A"),
            "current_hash": diff.get("current", "N/A"),
            "object_repr": repr(diff.get("obj", "N/A"))[:500]  # 限制长度
        }
        if "error" in diff:
            case_data["error"] = diff["error"]
        save_data["inconsistent_cases"].append(case_data)
    
    # 保存为 JSON 文件
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(save_data, f, indent=2, ensure_ascii=False)
    
    print(f"\n不一致结果已保存到: {filepath}")
    
    # 同时保存一个易读的文本文件
    txt_filename = f"inconsistent_{version_safe}_{timestamp}.txt"
    txt_filepath = os.path.join(output_dir, txt_filename)
    
    with open(txt_filepath, "w", encoding="utf-8") as f:
        f.write("=" * 80 + "\n")
        f.write("Marshal 往返哈希值兼容性测试 - 不一致结果报告\n")
        f.write("=" * 80 + "\n\n")
        f.write(f"测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"当前 Python 版本: {current_version}\n")
        f.write(f"基准 Python 版本: 3.13.13\n")
        f.write(f"不一致用例总数: {len(differences)}\n")
        f.write("\n" + "=" * 80 + "\n\n")
        
        for i, diff in enumerate(differences, 1):
            f.write(f"[{i}] 测试用例: {diff['name']}\n")
            f.write(f"    基准哈希 (Python 3.13): {diff.get('baseline', 'N/A')}\n")
            f.write(f"    当前哈希 ({current_version}): {diff.get('current', 'N/A')}\n")
            if "error" in diff:
                f.write(f"    错误: {diff['error']}\n")
            else:
                f.write(f"    对象: {repr(diff.get('obj', 'N/A'))[:200]}\n")
            f.write("\n")
    
    print(f"易读文本版本已保存到: {txt_filepath}")
    
    return filepath, txt_filepath


def run_compatibility_test():
    """运行兼容性测试"""
    print("=" * 70)
    print("Marshal 往返哈希值兼容性测试")
    print(f"当前 Python 版本: {sys.version}")
    print("=" * 70)
    
    # 获取当前版本信息
    current_version = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
    current_version_full = sys.version.split()[0]
    
    # 收集所有测试用例
    all_test_cases = []
    all_test_cases.extend(_get_determinism_test_cases())
    all_test_cases.extend(_get_recursive_test_cases())
    all_test_cases.extend(_get_boundary_test_cases())
    all_test_cases.extend(_get_whitebox_test_cases())
    all_test_cases.extend(_get_fuzzing_test_cases(fuzz_count=100, seed=42))
    
    print(f"\n总测试用例数: {len(all_test_cases)}")
    
    # 比较哈希值
    passed = 0
    failed = 0
    missing_in_baseline = 0
    extra_in_baseline = 0
    
    differences = []
    
    print("\n" + "-" * 70)
    print("比较结果:")
    print("-" * 70)
    
    current_hashes = {}
    
    for name, obj in all_test_cases:
        try:
            restored = safe_marshal_roundtrip(obj)
            current_hash = hash_object(restored)
            current_hashes[name] = current_hash
            
            if name in MARSHAL_ROUNDTRIP_BASELINE_HASHES:
                baseline_hash = MARSHAL_ROUNDTRIP_BASELINE_HASHES[name]
                
                if current_hash == baseline_hash:
                    passed += 1
                    print(f"  ✓ {name}: 一致")
                else:
                    failed += 1
                    differences.append({
                        "name": name,
                        "current": current_hash,
                        "baseline": baseline_hash,
                        "obj": obj
                    })
                    print(f"  ✗ {name}: 不一致")
                    print(f"      当前: {current_hash}")
                    print(f"      基准: {baseline_hash}")
            else:
                missing_in_baseline += 1
                print(f"  ? {name}: 不在基准哈希中")
                
        except Exception as e:
            failed += 1
            differences.append({
                "name": name,
                "current": None,
                "baseline": MARSHAL_ROUNDTRIP_BASELINE_HASHES.get(name, "N/A"),
                "error": str(e),
                "obj": obj
            })
            print(f"  ✗ {name}: 错误 - {e}")
    
    # 检查基准中是否有当前测试没有的用例
    for name in MARSHAL_ROUNDTRIP_BASELINE_HASHES:
        if name not in current_hashes:
            extra_in_baseline += 1
            print(f"  ? {name}: 基准中存在但当前测试未生成")
    
    # 打印总结
    print("\n" + "=" * 70)
    print("测试总结")
    print("=" * 70)
    print(f"通过: {passed}")
    print(f"失败: {failed}")
    print(f"不在基准中: {missing_in_baseline}")
    print(f"基准中多余: {extra_in_baseline}")
    print(f"总计: {len(all_test_cases)}")
    print(f"成功率: {passed/(passed+failed)*100:.2f}%" if (passed+failed) > 0 else "N/A")
    
    # 打印差异详情
    if differences:
        print("\n" + "=" * 70)
        print(f"差异详情 (共 {len(differences)} 个)")
        print("=" * 70)
        
        for i, diff in enumerate(differences, 1):
            print(f"\n{i}. {diff['name']}")
            if 'error' in diff:
                print(f"   错误: {diff['error']}")
            else:
                print(f"   当前哈希: {diff['current']}")
                print(f"   基准哈希: {diff['baseline']}")
                print(f"   对象: {repr(diff['obj'])[:200]}")
    
    # 保存不一致的结果
    if differences:
        print("\n" + "=" * 70)
        print("保存不一致结果...")
        print("=" * 70)
        save_inconsistent_results(current_version_full, differences)
    
    # 判断兼容性
    print("\n" + "=" * 70)
    if failed == 0 and missing_in_baseline == 0 and extra_in_baseline == 0:
        print("✓ 兼容性测试通过！当前环境的 marshal 行为与基准完全一致。")
    else:
        print("✗ 兼容性测试失败！当前环境的 marshal 行为与基准存在差异。")
        if failed > 0:
            print(f"  有 {failed} 个用例的哈希值不匹配")
        if missing_in_baseline > 0:
            print(f"  有 {missing_in_baseline} 个用例不在基准中")
        if extra_in_baseline > 0:
            print(f"  有 {extra_in_baseline} 个基准用例在当前测试中缺失")
    print("=" * 70)
    
    return passed, failed, differences


if __name__ == "__main__":
    run_compatibility_test()