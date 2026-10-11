        // Authored diagnostic-only optimizer arm. Main/import/export unchanged.
        let mode = std::fs::read_to_string("audit-native-mode.txt").unwrap();
        let (angle, first, second): (f32, (f32, f32), (f32, f32)) = match mode.trim() {
            "contact_decimal_0" => (0.0, (0.5, 1.0), (1.5, 1.0)),
            "gap_margin_0" => (0.0, (0.5, 1.0), (1.501, 1.0)),
            "overlap_margin_0" => (0.0, (0.5, 1.0), (1.499, 1.0)),
            "continuous37_gap" => (37.0, (1.0, 1.0), (3.0, 1.0)),
            _ => panic!("audit_unknown_mode"),
        };
        assert_eq!(self.instance.total_item_qty(), 2);
        assert_eq!(self.instance.item_qty(0), 2);
        self.problem.change_strip_width(5.0);
        let item = self.instance.item(0);
        let original = item.shape_orig.shape.vertices.iter().map(|p| {
            serde_json::json!([p.x(), p.y(), p.x().to_bits(), p.y().to_bits()])
        }).collect::<Vec<_>>();
        let internal_shape = item.shape_cd.vertices.iter().map(|p| {
            serde_json::json!([p.x(), p.y(), p.x().to_bits(), p.y().to_bits()])
        }).collect::<Vec<_>>();
        let pre = item.shape_orig.pre_transform;
        let mut transforms = Vec::new();
        for tr in [first, second] {
            let exterior = jagua_rs::io::ext_repr::ExtTransformation {
                rotation: angle, translation: tr,
            };
            let exterior_dt: jagua_rs::geometry::DTransformation = exterior.into();
            let interior = jagua_rs::io::import::ext_to_int_transformation(&exterior_dt, &pre);
            transforms.push(serde_json::json!({
                "rotation_radians": interior.rotation(),
                "rotation_bits": interior.rotation().to_bits(),
                "translation": interior.translation(),
                "translation_bits": [interior.translation().0.to_bits(), interior.translation().1.to_bits()],
                "roundtrip": jagua_rs::io::ext_repr::ExtTransformation::from(
                    jagua_rs::io::export::int_to_ext_transformation(&interior, &pre)),
            }));
            self.problem.place_item(SPPlacement { item_id: 0, d_transf: interior });
        }
        let diagnostic = serde_json::json!({
            "schema": "jagua-authored-native-contours-v1", "mode": mode.trim(),
            "numeric_storage": "Rust f32; bit patterns accompany contour and transform measurements",
            "shape_orig": original, "shape_cd": internal_shape,
            "pre_transform": {
                "rotation_radians": pre.rotation(), "rotation_bits": pre.rotation().to_bits(),
                "translation": pre.translation(),
                "translation_bits": [pre.translation().0.to_bits(), pre.translation().1.to_bits()],
            },
            "internal_transforms": transforms,
            "allowed_rotation_debug": format!("{:?}", item.allowed_rotation),
            "cde_is_feasible": self.problem.layout.is_feasible(),
            "strip_width": self.problem.strip_width(),
        });
        std::fs::write("audit-native-contours.json", serde_json::to_vec(&diagnostic).unwrap()).unwrap();
        return self.problem.save();
