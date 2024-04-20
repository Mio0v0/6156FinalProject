using System;
using System.Collections;
using System.Collections.Generic;
using UnityEngine;
using UnityEditor;
using Valve.VR;
using Valve.VR.InteractionSystem;
using LSL;
using Random = System.Random;
using System.Threading;
using ReNa;
using NaughtyAttributes;

public class RSVPController : MonoBehaviour
{
    [HideInInspector]
    public float preEvalWaitTime, postEvalWaitTime, postTutorialWaitTime;

    [Header("Session parameters")]
    [MinMaxSlider(1, 10)]
    public Vector2Int numOfTargetRange;
    [MinMaxSlider(0, 10)]
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
    public ItemManagerScript itemManager;
    public UIController uiController;
    public GameObject fixationDot;
    public SessionLog sessionLog;
    public EEGDetectionManager eegDetectionManager;
    public EEGVerificationManager eegVerificationManager;

    [Header("In-game parameters (READ ONLY)")]
    public int numOfTarget;
    public int numOfNovelty;
    public GameObject target;
    public List<GameObject> itemList;
    public string gameState = WAITINGIDLE;
    public int currentBlockID;

    #region define game states
    private static string STARTED = "started";
    private static string WAITINGSHOWINGOBJECTS = "waiting";
    private static string WAITINGIDLE = "waitingIdle";
    private static string BlockEND = "groupEnded";
    #endregion

    void Start()
    {
        itemCount = 1;

        preEvalWaitTime = sessionScript.preEvalDuration;
        postEvalWaitTime = sessionScript.postEvalDuration;
        postTutorialWaitTime = sessionScript.postTutorialDuration;
    }

    void OnEnable()
    {
        gameState = STARTED; //start w/o learning period
        Debug.Log("RSVP Started: Target item name: "+ itemManager.GetCurrentTargetItem().name);
    }

    void Update()
    {
        // STARTED -->  INTRIAL --> Likert eval --> intertrial wait --> next in-trail
        if (gameState == STARTED)
        {
            // start block here
            numOfTarget = UnityEngine.Random.Range(numOfTargetRange.x, numOfTargetRange.y);
            numOfNovelty = UnityEngine.Random.Range(numOfNoveltyRange.x, numOfNoveltyRange.y);
            Dictionary<string, List<double>> blockItemRoleCatalogDict = itemManager.StartBlock(sessionScript.numItemsPerBlock, numOfTarget, numOfNovelty);
            
            currentBlockID = sessionLog.StartBlockAndLogItems(blockItemRoleCatalogDict);
            sessionScript.InsertEventMarkers(new List<string> { "BlockIDStartEnd", "BlockMarker" },
                new List<double> { (double)currentBlockID, 1 });

            itemList = new List<GameObject>();
            int i = 0;
            foreach (GameObject item in itemManager.GetMiniBlockItems(sessionScript.numItemsPerBlock))
            {
                GameObject newItem = (GameObject)Instantiate(item, Vector3.zero, item.transform.rotation);
                newItem.SetActive(false);
                if (newItem.GetComponent<Rigidbody>() != null)
                {
                    newItem.GetComponent<Rigidbody>().useGravity = false;
                    newItem.GetComponent<Rigidbody>().isKinematic = true;
                }
                if (newItem.GetComponent<RSVPFade>() == null) newItem.AddComponent<RSVPFade>();
                newItem.GetComponent<RSVPFade>().sessionScript = sessionScript;
                newItem.GetComponent<RSVPFade>().itemManager = itemManager;
                Utils.ProcessForward(newItem);
                newItem.AddComponent<ReNaItem>();
                newItem.GetComponent<ReNaItem>().itemIndexInBlock = i++;

                itemList.Add(newItem);
            }
            Debug.Log(string.Format("RSVP: Target catalog value is {0}", itemManager.GetItemCatalogValue(itemManager.currentTargetItem)));

            StartCoroutine(InitialWaitCoroutine());
            gameState = WAITINGSHOWINGOBJECTS; //do nothing when waiting
        }
        else if (gameState == WAITINGSHOWINGOBJECTS)
        {
            //do nothing
        }
        else if (gameState == WAITINGIDLE)
        {
            //do nothing, while 
        }

        if (gameState == BlockEND) // when block ends
        {
            gameState = WAITINGSHOWINGOBJECTS;
            StartCoroutine(endBlockCoroutine());
        }

        fixationDot.GetComponent<FixationPointController>().SetVisible(!isSomethingShowing() && gameState != "WaitingEvaluation");
        fixationDot.transform.position = Camera.main.transform.position + 0.5f *(distFromPlayerRange.y + distFromPlayerRange.x) * Vector3.forward;
    }

    private IEnumerator InitialWaitCoroutine()
    {
        fixationDot.GetComponent<FixationPointController>().StartFacingCounter(20, 1.5f);
        while (!fixationDot.GetComponent<FixationPointController>().isCounterReached)
        {
            yield return null;
        }
        StartCoroutine(waitToShowItemCoroutine(itemList.Count - 1));
    }

    private IEnumerator waitToShowItemCoroutine(int currentItemIndex)
    {
        float interItemDuration = UnityEngine.Random.Range(interItemDurationRange.x, interItemDurationRange.y);
        yield return new WaitForSeconds(interItemDuration);
        presentationAudio.Play();
        itemList[currentItemIndex].GetComponent<RSVPFade>().PrepareToShow(UnityEngine.Random.Range(distFromPlayerRange.x, distFromPlayerRange.y), itemOnScreenDuration);
        Debug.Log(string.Format("RSVP: Presenting item catalog value is {0}, Items remaining is {1}", itemManager.GetItemCatalogValue(itemList[currentItemIndex]), currentItemIndex));

        // Detection
        eegDetectionManager.DetectEEGChanges(itemList[currentItemIndex]);

        currentItemIndex -= 1;
        if (currentItemIndex < 0)
        {
            gameState = BlockEND;
        }
        else
        {
            yield return new WaitForSeconds(itemOnScreenDuration);
            StartCoroutine(waitToShowItemCoroutine(currentItemIndex));
        }
    }

    private IEnumerator endBlockCoroutine()
    {
        yield return new WaitForSeconds(sessionScript.preEvalDuration);
        blockEndAudio.Play();
        gameState = WAITINGIDLE;
        sessionScript.InsertEventMarkers("BlockIDStartEnd", -(double)currentBlockID); // signal the end of the block

        // Verification
        eegVerificationManager.VerifyEEGChanges();

        uiController.SetUpEvaluation("RSVP", gameObject, numOfTarget);
        Debug.Log("RSVPController: RSVP block ended, entering participant evaluation");
    }

    public bool isSomethingShowing()
    {
        bool rtn = false;
        if (itemList == null)
        {
            rtn = false;
        }
        else
        {
            foreach (GameObject item in itemList)
            {
                if (item != null)
                {
                    rtn |= item.GetComponent<RSVPFade>().isShowing;
                }
            }
        }
        return rtn;
    }
}