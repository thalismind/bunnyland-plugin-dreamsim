"""Optional, lazily imported 3D appearance for beds."""

from .components import BedComponent


def install_dreamsim_3d(actor, context) -> None:
    if context.plugins is None or not context.plugins.enabled("bunnyland.3d"):
        return
    from bunnyland_3d import (
        EntityVisualContribution,
        EntityVisualRule,
        ModelAsset,
        ModelTransform,
        PrimitivePart3D,
        ProceduralModelSource,
        VisualMaterial3D,
        register_entity_visuals,
        register_models,
    )

    owner = "bunnyland.dreamsim"
    model_key = f"{owner}/bed"
    register_models(
        actor,
        owner,
        (
            ModelAsset(
                key=model_key,
                source=ProceduralModelSource(
                    parts=(
                        PrimitivePart3D(
                            "frame",
                            "box",
                            size=(1.5, 0.2, 2.2),
                            transform=ModelTransform(translation=(0, 0.25, 0)),
                            material=VisualMaterial3D(color="#6b442d"),
                            roles=("damageable",),
                        ),
                        PrimitivePart3D(
                            "mattress",
                            "box",
                            size=(1.4, 0.28, 2.05),
                            transform=ModelTransform(translation=(0, 0.47, 0)),
                            material=VisualMaterial3D(color="#d9d4bd"),
                        ),
                        PrimitivePart3D(
                            "pillow",
                            "capsule",
                            radius=0.22,
                            height=0.65,
                            transform=ModelTransform(
                                rotation=(0, 0, 1.5708), translation=(0, 0.72, -0.65)
                            ),
                            material=VisualMaterial3D(color="#f1ead7"),
                            roles=("state-indicator",),
                        ),
                        PrimitivePart3D(
                            "headboard",
                            "box",
                            size=(1.55, 1.0, 0.14),
                            transform=ModelTransform(translation=(0, 0.72, -1.05)),
                            material=VisualMaterial3D(color="#6b442d"),
                        ),
                    )
                ),
            ),
        ),
    )
    register_entity_visuals(
        actor,
        owner,
        (
            EntityVisualRule(
                key=f"{owner}/bed",
                predicate=lambda entity: entity.has_component(BedComponent),
                contribution=EntityVisualContribution(base_model_key=model_key),
            ),
        ),
    )


__all__ = ["install_dreamsim_3d"]
