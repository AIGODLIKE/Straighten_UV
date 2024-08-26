from Straighten_UV.common.class_loader.auto_load import preprocess_dictionary

dictionary = {
    "zh_CN": {
        # ("*", "straighten UV"): "拉直UV",
        ("*", "Straighten UV"): "拉直UV",
        ("*", "Straighten UV."): "拉直UV",
        ("*", "Relax"): "松弛",
        ("*", "Uv Straighten"): "拉直UV",
        ("*", "Align and straighten according to the selected direction"): "根据选择的方向对齐拉直",
        ("*", "straighten line uv(→)"): "拉直线(→)",
        ("*", "straighten line uv(←)"): "拉直线(←)",
        ("*", "straighten line uv(↑)"): "拉直线(↑)",
        ("*", "straighten line uv(↓)"): "拉直线(↓)",
        ("*", "unwrap island uv"): "展开uv岛（放松）",
        ("*", "Unwrap Island"): "展开uv岛（放松）",
        ("*", "unwrap selected uv"): "展开选中的uv",
        ("*", "Unwrap Selected"): "展开选中的uv",
        # This is not a standard way to define a translation, but it is still supported with preprocess_dictionary.
        "Boolean Config": "布尔参数",
        ("*", "Add-on Preferences View"): "插件设置面板",
        ("Operator", "Straighten_UV"): "拉直UV",
        ("Operator", "Straighten UV"): "拉直UV",
    }
}

dictionary = preprocess_dictionary(dictionary)

dictionary["zh_HANS"] = dictionary["zh_CN"]
