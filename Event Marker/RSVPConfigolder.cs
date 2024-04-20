using NaughtyAttributes;
using System.Collections;
using System.Collections.Generic;
using UnityEngine;

// This script holds all configurations for RSVP condition
public class RSVPConfigolder : MonoBehaviour
{
    [HideInInspector]
    public float preEvalWaitTime, postEvalWaitTime, postTutorialWaitTime;

    [Header("Session parameters")]
    [MinMaxSlider(1, 10)]
    public Vector2Int numOfTargetRange;
    [MinMaxSlider(1, 10)]
    public Vector2Int numOfNoveltyRange;

    [HideInInspector]
    public int numOfBlocks, itemCount;

    [Header("Offset parameters")]
    [MinMaxSlider(0, 20)]
    public Vector2 distFromPlayerRange;

    [Header("Time settings")]
    public float itemOnScreenDuration;
    [MinMaxSlider(0, 5)]
    public Vector2 interItemDurationRange;

    [Header("Other game objects (don't change unless you know what you're doing)")]
    public AudioSource blockEndAudio; 
    public AudioSource presentationAudio;
    public SessionParam sessionScript;
    public RSVPController rsvpScript;
    public ItemManagerScript itemManager;
    public UIController uiController;
    public GameObject fixationDot;


    void Start()
    {
        itemCount = 1;

        preEvalWaitTime = sessionScript.preEvalDuration;
        postEvalWaitTime = sessionScript.postEvalDuration;
        postTutorialWaitTime = sessionScript.postTutorialDuration;

        rsvpScript.numOfTargetRange = numOfTargetRange;
        rsvpScript.numOfNoveltyRange = numOfNoveltyRange;

        rsvpScript.postTutorialWaitTime = postTutorialWaitTime;
        rsvpScript.preEvalWaitTime = preEvalWaitTime;
        rsvpScript.postEvalWaitTime = postEvalWaitTime;

        //rsvpScript.numOfGroups = numOfBlocks;

        rsvpScript.itemCount = itemCount; // num of item in one trial
        rsvpScript.distFromPlayerRange = distFromPlayerRange;

        rsvpScript.blockEndAudio = blockEndAudio; //pre-trail audio
        rsvpScript.presentationAudio = presentationAudio; // post-trail audio

        rsvpScript.itemManager = itemManager;
        rsvpScript.uiController = uiController;

        rsvpScript.itemOnScreenDuration = itemOnScreenDuration;
        rsvpScript.interItemDurationRange = interItemDurationRange;
        rsvpScript.fixationDot = fixationDot;
    }

}